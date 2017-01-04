from collections import deque

class EditState(object):
    '''
    This class holds exactly how many attributes are needed
    for what we need to describe most undo and redo states.

    The reason for the use of slots is that thousands of these may
    be needed per window, and that may take up a considerable amount
    of ram at some point. This is merely an optimization.
    '''
    __slots__ = (
        "nodepath",  # Path to the node which is being edited
        #              This path is a list of attr_indices, which will usually
        #              be integers, but may also be strings(such as 'STEPTREE')
        #              This is used for locating the widget and node to update.
        "edit_type",  # A string that tells the widget what type of edit
        #               must be applied(ex: "array_shift", "replace", etc)
        "apply_func",  # The function to call to apply the edit to the widget
        "attr_index",  # The index into the parent that the node to edit is at
        "undo_node",  # When undoing, this is the node data to replace with
        "redo_node",  # When redoing, this is the node data to replace with
        "tag_window",  # The TagWindow which the edit belongs to
        "desc",  # The descriptor used by the FieldWidget and node.
        #          Used to determine if a widget is the one being looked for
        "edit_info",  # A freeform entry that only exists to hold
        #               extra information that a widget may need
        #               to better describe the undo/redo operation
        )

    def __init__(self, *args, **kwargs):
        self.desc = kwargs.pop('desc', None)
        self.nodepath = kwargs.pop('nodepath', None)
        self.edit_type = kwargs.pop('edit_type', None)
        self.apply_func = kwargs.pop('apply_func', None)
        self.attr_index = kwargs.pop('attr_index', None)
        self.undo_node = kwargs.pop('undo_node', None)
        self.redo_node = kwargs.pop('redo_node', None)
        self.tag_window = kwargs.pop('tag_window', None)
        if kwargs:
            if args:
                kwargs['args'] = args
            self.edit_info = kwargs
        elif args:
            self.edit_info = {i: args[i] for i in range(len(args))}
        else:
            self.edit_info = None

class EditManager(object):
    _edit_states = None

    # The index of the edit_states that a new undo will be added into
    # This means when undoing, edit_states[edit_index-1] should be
    # returned, and when redoing, edit_states[edit_index] should be.
    _edit_index = 0

    @property
    def edit_index(self):
        return self._edit_index

    @property
    def maxlen(self):
        return self._edit_states.maxlen

    def __init__(self, max_states=100):
        self._edit_states = deque(maxlen=max_states)

    def undo(self):
        i = self._edit_index
        if i <= 0 or not len(self._edit_states):
            return
        self._edit_index -= 1
        return self._edit_states[i-1]

    def redo(self):
        i = self._edit_index
        if i >= len(self._edit_states):
            return
        self._edit_index += 1
        return self._edit_states[i]

    def add_state(self, new_state):
        states = self._edit_states
        if self._edit_index < len(states):
            # slice off states at the current undo index
            states = deque((states[i] for i in range(self._edit_index)),
                           maxlen=states.maxlen)
        states.append(new_state)
        self._edit_states = states
        self._edit_index = len(states)

    def clear(self):
        self._edit_states.clear()
        self._edit_index = 0

    def resize(self, maxlen):
        states = self._edit_states
        new_states = deque(states, maxlen=maxlen)
        self._edit_states = new_states
        self._edit_index -= len(states) - len(new_states)
