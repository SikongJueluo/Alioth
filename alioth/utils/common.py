from astrbot.api.star import Star

global_plugin_context: Star._ContextLike


def initialize_utils_common(context: Star._ContextLike):
    global global_plugin_context
    global_plugin_context = context
