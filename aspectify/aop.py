# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_aop.ipynb.

# %% auto 0
__all__ = ['is_detectable', 'advice', 'Aspect']

# %% ../nbs/00_aop.ipynb 3
import re
import logging

from functools import wraps

# %% ../nbs/00_aop.ipynb 4
def is_detectable(name, # The name of the object.
                  obj # The builded object (potentially class).
                 ):
    """
    Determines when an object is potentially detectable to add an aspect to it.
    """
    return (
        name not in ["get_ipython", "exit", "quit", "open"]
        and not isinstance(obj, Aspect)
        and isinstance(obj, type) # it must be a type (a class)
        and callable(obj)
            )

# %% ../nbs/00_aop.ipynb 5
def advice(moment: str, # One of 'before', 'around', 'after_returning', 'after_throwing' or 'after'. See the documentation for more information.
           todo: object, # What to do at the selected moment.
           use_reference: bool = False # Whether to use or not the referenced object, used when the catched method is not a class method.
          ):
    """
    Add an advice to a particular function.
    """
    def dec(method):
        @wraps(method)
        def inner(*args, **kwargs):
            if moment not in ["before", "around", "after_returning", "after_throwing", "after"]:
                raise Exception(f"Moment {moment} is not defined.")
            
            obj_ref = [args[0]]
            todo_args = args if use_reference else args[1:]
                
            try:
                if moment == "before":
                    logging.info("Executed 'before' todo method")
                    new_args = todo(*todo_args, **kwargs)
                    if new_args:
                        logging.warning(f"Args changed from {list(args)} to {obj_ref + new_args}")
                        args = obj_ref + new_args
                        todo_args = new_args

                 
                if moment == "around":
                    logging.info("Executed 'around' todo method")
                    result = todo(*todo_args, **kwargs) 
                else:
                    result = method(*args, **kwargs)
                
                if moment in ["after_returning", "after"]:
                    logging.info("Executed 'after_returning' or 'after' todo method")
                    todo(*todo_args, **kwargs)
                    
                return result

            except Exception as e:
                if moment in ["after_throwing", "after"]:
                    logging.info("Executed 'after_throwing' or 'after' todo method")
                    todo(e, *todo_args, **kwargs)

                raise e

        return inner
    return dec

# %% ../nbs/00_aop.ipynb 6
class Aspect():
    """
    Defines a complete aspect.
    """
    def __init__(self):
        """
        Defines a new aspect.
        """
        self.before = None
        self.around = None
        self.after_returning = None
        self.after_throwing = None
        self.after = None

    # POINTCUT
    def create_pointcut(self,
                        objects, # All the classes to which the aspect can be added. See the documentation for more information.
                        pattern, # The pattern (string that defines a regular expression) used to select the methods to be added the aspect.
                        logging = True # Whether to log the captured methods with the `PointCut`.
                       ):
        """
        Creates a new pointcut associated with the aspect.
        """
        pattern = re.compile(pattern)

        for name, _object in objects:
            if is_detectable(name, _object):
                for method_name in dir(_object):
                    if "__" in method_name: continue
                    
                    full_method_name = str(_object.__module__) + "." + str(_object.__qualname__) + "." + method_name
                    if pattern.fullmatch(full_method_name):
                        # logs the method if requested
                        if logging: message = "Captured method: " + full_method_name
                        
                        # gets the method
                        method = getattr(_object, method_name)

                        # modifies it
                        if self.around: method = advice("around", self.around)(method) # we need to add the around modification first. If not, it will overwrite the other methods
                        if self.before: method = advice("before", self.before)(method)
                        if self.after_returning: method = advice("after_returning", self.after_returning)(method)
                        if self.after_throwing: method = advice("after_throwing", self.after_throwing)(method)
                        if self.after: method = advice("after", self.after)(method)

                        # saves it
                        try:
                            setattr(_object, method_name, method)
                        except AttributeError as e:
                            if logging: message += "; CANNOT be modified."
                        
                        if logging: print(message)

    # ADVICES
    def set_before(self,
                   function # The 'to do' function in that moment.
                  ):
        """
        Determines what to do before the execution of the method.
        """
        self.before = function
    
    def set_around(self,
                   function # The 'to do' function in that moment.
                  ):
        """
        Determines what to do instead of the execution of the method.
        """
        self.around = function
    
    def set_after_returning(self,
                            function # The 'to do' function in that moment.
                           ):
        """
        Determines what to do after a complete execution of the method (when there are not exceptions).
        """
        self.after_returning = function
    
    def set_after_throwing(self,
                           function # The 'to do' function in that moment.
                          ):
        """
        Determines what to do when the execution of the method raises an exception.
        
        * BEWARE! This method will not handle the exception (it will be finally raised), but it will allow you to do something when the exception is raised.
        """
        self.after_throwing = function

    def set_after(self,
                  function # The 'to do' function in that moment.
                 ):
        """
        Determines what to do after the execution of the method. This function will be always executed after the `after_returning` and `after_throwing` functions.
        """
        self.after = function
