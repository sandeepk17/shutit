import curtsies
import time
import threading
import traceback
import sys


# TODO: reject tmux sessions - it does not seem to play nice
# TODO: keep a time counter after the line
# TODO: show context of line (ie lines around)
# TODO: put the lines into an array of objects and mark the lines as inverted/not
# TODO: Split the pane into two and show line in top and context in bottom
def gather_module_paths():
	import shutit_global
	shutit_global_object = shutit_global.shutit_global_object
	owd = shutit_global_object.owd
	shutit_module_paths = set()
	for shutit_object in shutit_global.shutit_global_object.shutit_objects:
		shutit_module_paths = shutit_module_paths.union(set(shutit_object.host['shutit_module_path']))
	if '.' in shutit_module_paths:
		shutit_module_paths.remove('.')
		shutit_module_paths.add(owd)
	for path in shutit_module_paths:
		if path[0] != '/':
			shutit_module_paths.remove(path)
			shutit_module_paths.add(owd + '/' + path)
	return shutit_module_paths

def managing_thread_main():
	import shutit_global
	from shutit_global import SessionPaneLine
	# TODO: only do this when ready
	time.sleep(1)
	shutit_module_paths = gather_module_paths()
	shutit_global.shutit_global_object.stacktrace_lines_arr = [SessionPaneLine('',time.time(),'log'),]
	while True:
		# Acquire lock to write screen. Prevents nasty race conditions.
		if shutit_global.shutit_global_object.global_thread_lock.acquire(False):
			# Go to sleep if we can't get the lock as spinning causes 100% CPU
			time.sleep(0.1)
			continue
		code = []
		for thread_id, stack in sys._current_frames().items():
			# ignore own thread:
			if thread_id == threading.current_thread().ident:
				continue
			for filename, lineno, name, line in traceback.extract_stack(stack):
				# if the file is in the same folder or subfolder as a folder in: self.host['shutit_module_path']
				# then show that context
				for shutit_module_path in shutit_module_paths:
					if filename.find(shutit_module_path) == 0:
						line = '===> ' + str(line.strip())
						if shutit_global.shutit_global_object.stacktrace_lines_arr[-1] != line:
							code.append('=> %s:%d:%s' % (filename, lineno, name))
							code.append('%s' % (line,))
		for line in code:
			shutit_global.shutit_global_object.stacktrace_lines_arr.append(SessionPaneLine(line,time.time(),'log'))
		shutit_global.shutit_global_object.pane_manager.draw_screen(draw_type='default')
		shutit_global.shutit_global_object.global_thread_lock.release()


def track_main_thread():
	t = threading.Thread(target=managing_thread_main)
	t.daemon = True
	t.start()


def managing_thread_main_simple():
	import shutit_global
	last_msg = ''
	while True:
		printed_anything = False
		if shutit_global.shutit_global_object.log_trace_when_idle and time.time() - shutit_global.shutit_global_object.last_log_time > 5:
			this_msg = ''
			for thread_id, stack in sys._current_frames().items():
				# ignore own thread:
				if thread_id == threading.current_thread().ident:
					continue
				printed_thread_started = False
				for filename, lineno, name, line in traceback.extract_stack(stack):
					if not printed_anything:
						printed_anything = True
						this_msg += '='*80 + '\n'
						this_msg += 'STACK TRACES PRINTED ON IDLE: THREAD_ID: ' + str(thread_id) + '\n'
						this_msg += '='*80 + '\n'
					if not printed_thread_started:
						printed_thread_started = True
					this_msg += '%s:%d:%s' % (filename, lineno, name) + '\n'
					if line:
						this_msg += '  %s' % (line,) + '\n'
			if printed_anything:
				this_msg += '='*80 + '\n'
				this_msg += 'STACK TRACES DONE\n'
				this_msg += '='*80 + '\n'
			if this_msg != last_msg:
				print(this_msg)
				last_msg = this_msg
			else:
		time.sleep(5)
	

def track_main_thread_simple():
	t = threading.Thread(target=managing_thread_main_simple)
	t.daemon = True
	t.start()
