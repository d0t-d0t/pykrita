from PyQt5.QtCore import QTimer, QEventLoop
from .OT_debug_tools import draw_info
from krita import *
k= Krita.instance()
current_layer = None

# sem = QSemapahore(1)
verbose=False
timer_offest = 0

global_sleep_time=0

def sleep(value=100,act = None,increment_value=False): 
    if increment_value:  
        global global_sleep_time 
        value += global_sleep_time
        global_sleep_time = value
    need_exec = False 
    if not act:
        loop = QEventLoop()
        act = loop.quit

        need_exec=True
    QTimer.singleShot(global_sleep_time,act )
    if need_exec:
        loop.exec()


def get_timer(func,time=150):
    timer =  QTimer()
    timer.setInterval(time)  # I found that is a golden center in terms of waiting time
    timer.setSingleShot(True)
    timer.timeout.connect(func)
    timer.singleShot(time,func )
    return timer

def wait_for_completion(condition_func):
    loop = QEventLoop()
    timer_timeout = QTimer()

    def check_condition():
        if condition_func():
            loop.quit()  # Exit the event loop when the condition is met

    timer_timeout.timeout.connect(check_condition)
    timer_timeout.start(100)  # Check every 100 milliseconds
    loop.exec_()  # Enter the Qt event loop to wait for the condition

# def wait_for_completion(condition_func):
#     loop = QEventLoop()
#     timer = QTimer()
#     timer.setSingleShot(True)
#     timer.timeout.connect(loop.quit)

#     def check_condition():
#         if condition_func():
#             timer.start(0)  # Trigger the timeout to quit the event loop


#     timer_timeout = QTimer()
#     timer_timeout.setInterval(10000)
#     timer_timeout.timeout.connect(check_condition)

#     timer_timeout.start()
#     loop.exec()

def basic_condition_func():
    # Define a generic condition that checks if the operation is complete
    d = k.activeDocument()
    d.waitForDone()
    return True

def has_active_node_changed():
    # if verbose:draw_info("Infinite loop...")

    # return False
    d = k.activeDocument()
    global current_layer
    result = d.activeNode() and (d.activeNode().name() != current_layer.name())

    # Define a generic condition that checks if the operation is complete
    return  result


def perform_krita_operation(operation_func, *args,
                            timing=150,
                            condition_type='basic',
                             callback=None, **kwargs):
    # sem.aquire(1)
    match condition_type:
        case 'basic':
            condition_func = basic_condition_func
        case 'lyr_change':
            global current_layer
            d= k.activeDocument()
            current_layer = d.activeNode()
            condition_func = has_active_node_changed
        



    def wrapped_operation():
        result = operation_func(*args, **kwargs)
        if callback:
            QTimer.singleShot(timing, lambda: callback(result))
        return result

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(lambda: wait_for_completion(condition_func))
    timer.start(0)  # Start the timer to execute the operation
    
    
    perform_timer = QTimer()
    perform_timer.setSingleShot(True)
    if verbose:draw_info('Performing operation...')

    perform_timer.timeout.connect(wrapped_operation)
    # global timer_offest
    # timing +=timer_offest
    # timer_offest=timing
    perform_timer.start(timing)
    # sem.release(1)
    return wrapped_operation() 


'''
# Example usage within your Krita script
def select_opaque():
    action = k.action('selectopaque')
    action.trigger()

def example_script():
    d = k.activeDocument()
    currentLayer = d.activeNode()

    def callback(result):
        print("Operation completed with result:", result)
        # Proceed with other operations...

    perform_krita_operation(d, select_opaque, callback=callback)

# Another example with arguments and return value
def some_other_operation(param1, param2):
    # Perform some Krita operation with param1 and param2
    print(f"Performing operation with {param1} and {param2}")
    result = param1 + param2  # Just an example of a return value
    return result

def example_with_args():
    d = k.activeDocument()
    currentLayer = d.activeNode()

    def callback(result):
        print("Operation completed with result:", result)
        # Proceed with other operations...

    perform_krita_operation(d, some_other_operation, 5, 10, callback=callback)

# Run your example script
example_script()
example_with_args()'''