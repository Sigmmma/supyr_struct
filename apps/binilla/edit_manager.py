from collections import deque

class EditState(object):
    '''
    This class holds exactly how many attributes are needed
    for what we need to describe an undo and redo state.

    The reason for the use of slots is that thousands of these may
    be needed per window, and that may take up a considerable amount
    of ram at some point. This is merely an optimization.
    '''
    __slots__ = ()


class EditManager(object):
    edit_states = None

    # The index of the edit_states that a new undo will be added into
    # This means when undoing, edit_states[edit_index-1] should be
    # returned, and when redoing, edit_states[edit_index] should be.
    edit_index = 0

    def __init__(self, max_states=100):
        self.edit_states = deque(maxlen=max_states)

    def undo(self):
        i = self.edit_index
        if i <= 0 or not len(self.edit_states):
            return
        self.edit_index -= 1
        return self.edit_states[i-1]

    def redo(self):
        i = self.edit_index
        if i >= len(self.edit_states):
            return
        self.edit_index += 1
        return self.edit_states[i]

    def add_state(self, new_state):
        states = self.edit_states
        if self.edit_index < len(states):
            # slice off states at the current undo index
            states = deque((states[i] for i in range(self.edit_index)),
                           maxlen=states.maxlen)
        states.append(new_state)
        self.edit_states = states
        self.edit_index = len(states)

    def clear(self):
        self.edit_states.clear()
        self.edit_index = 0

    def resize(self, maxlen):
        states = self.edit_states
        new_states = deque(states, maxlen=maxlen)
        self.edit_states = new_states
        self.edit_index -= len(states) - len(new_states)
