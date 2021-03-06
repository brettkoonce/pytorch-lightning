# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping, ProgressBarBase, ProgressBar
from pytorch_lightning.utilities import rank_zero_warn
from pytorch_lightning.utilities.exceptions import MisconfigurationException


class CallbackConnector:

    def __init__(self, trainer):
        self.trainer = trainer

    def on_trainer_init(
            self,
            callbacks,
            checkpoint_callback,
            progress_bar_refresh_rate,
            process_position,
            default_root_dir,
            weights_save_path,
            resume_from_checkpoint
    ):
        self.trainer.resume_from_checkpoint = resume_from_checkpoint

        # init folder paths for checkpoint + weights save callbacks
        self.trainer._default_root_dir = default_root_dir or os.getcwd()
        self.trainer._weights_save_path = weights_save_path or self.trainer._default_root_dir

        # init callbacks
        self.trainer.callbacks = callbacks or []

        # configure checkpoint callback
        # it is important that this is the last callback to run
        # pass through the required args to figure out defaults
        checkpoint_callback = self.init_default_checkpoint_callback(checkpoint_callback)
        if checkpoint_callback:
            self.trainer.callbacks.append(checkpoint_callback)

        # TODO refactor codebase (tests) to not directly reach into these callbacks
        self.trainer.checkpoint_callback = checkpoint_callback

        # init progress bar
        self.trainer._progress_bar_callback = self.configure_progress_bar(
            progress_bar_refresh_rate, process_position
        )

    def init_default_checkpoint_callback(self, checkpoint_callback):
        if checkpoint_callback is True:
            checkpoint_callback = ModelCheckpoint(filepath=None)
        elif checkpoint_callback is False:
            checkpoint_callback = None

        return checkpoint_callback

    def configure_progress_bar(self, refresh_rate=1, process_position=0):
        progress_bars = [c for c in self.trainer.callbacks if isinstance(c, ProgressBarBase)]
        if len(progress_bars) > 1:
            raise MisconfigurationException(
                'You added multiple progress bar callbacks to the Trainer, but currently only one'
                ' progress bar is supported.'
            )
        elif len(progress_bars) == 1:
            progress_bar_callback = progress_bars[0]
        elif refresh_rate > 0:
            progress_bar_callback = ProgressBar(
                refresh_rate=refresh_rate,
                process_position=process_position,
            )
            self.trainer.callbacks.append(progress_bar_callback)
        else:
            progress_bar_callback = None

        return progress_bar_callback
