import os
print('VOSK_MODEL_PATH:', os.getenv('VOSK_MODEL_PATH'))
print('Exists:', os.path.isdir(os.getenv('VOSK_MODEL_PATH','')))
