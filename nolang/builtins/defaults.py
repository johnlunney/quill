
from nolang.builtins.io import magic_print
from nolang.module import W_Module
from nolang.builtins.exception import W_Exception
from nolang.builtins.spec import wrap_function, wrap_type
from nolang.builtins.core.reflect import get_current_frame, W_FrameWrapper


def wrap_module(name, functions):
    raise NotImplementedError


def default_builtins():
    # XXX all of this should be more streamlined
    reflect_module = W_Module('reflect', {'get_current_frame': 0},
        [wrap_function(get_current_frame)])
    frame_wrapper_tp = wrap_type(W_FrameWrapper)
    W_FrameWrapper.cls_w_type = frame_wrapper_tp
    core_module = W_Module('core', {'reflect': 0}, [reflect_module])

    return [magic_print, W_Exception], core_module