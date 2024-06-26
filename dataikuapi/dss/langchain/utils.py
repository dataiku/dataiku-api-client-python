from threading import RLock


class StopSequencesAwareStreamer:
    """ Helper class to enforce stop sequences when streaming
    """
    def __init__(self, stop_sequences, stop_sequences_enforcer):
        self.stop_sequences = stop_sequences or []
        self.stop_sequences_enforcer = stop_sequences_enforcer
        self.current_chunk = None
        self._current_chunk_lock = RLock()

    def append(self, chunk):
        """ Appends a chunk to the current one, or just sets it if None
        """
        with self._current_chunk_lock:
            if self.should_stop():
                return

            if not self.current_chunk:
                self.current_chunk = chunk
            else:
                self.current_chunk += chunk

    def should_stop(self):
        """ Checks if streaming should stop because a stop sequence was found

        :returns: True if a stop sequence is found in the current chunk
        """
        with self._current_chunk_lock:
            if not self.stop_sequences:
                return False
            if not self.current_chunk:
                return False

            # if a stop sequence is found, remove it from the current chunk
            cutoff_text = self.stop_sequences_enforcer(self.current_chunk.text, self.stop_sequences)
            if cutoff_text != self.current_chunk.text:
                self.current_chunk.text = cutoff_text
                if hasattr(self.current_chunk, 'message'):
                    self.current_chunk.message.content = cutoff_text
                return True
        return False

    def can_yield(self):
        """ Checks if a chunk is safe to yield

        :returns: True unless a partial stop sequence is found in the current chunk
        """
        with self._current_chunk_lock:
            if not self.current_chunk:
                return False

            for sequence in self.stop_sequences:
                if self._has_sequence_started(sequence):
                    return False

            # at this point we're sure that the current chunk contains none of the stop sequences
            return True

    def yield_(self, producer):
        """ Returns the current chunk and resets the current chunk

        :returns: the current chunk
        """
        with self._current_chunk_lock:
            chunk = producer(self.current_chunk)
            self.current_chunk = None
            return chunk

    def _has_sequence_started(self, sequence):
        """
        :returns: true if any of the stop sequences has started in the current chunk
        """
        for i in range(len(sequence)):
            if self.current_chunk.text.endswith(sequence[:i + 1]):
                return True
        return False
