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

from typing import Any, Callable, List, Optional, Union

from torch import Tensor, tensor

from torchmetrics.functional.text.wil import _wil_compute, _wil_update
from torchmetrics.metric import Metric


class WordInfoLost(Metric):
    r"""
    Word Information Lost (WordInfoLost_) is a metric of the performance of an automatic speech
    recognition system. This value indicates the percentage of words that were incorrectly predicted
    between a set of ground-truth sentences and a set of hypothesis sentences.
    The lower the value, the better the performance of the ASR system with a WordInfoLost of
    0 being a perfect score.
    Word Information Lost rate can then be computed as:

    .. math::
        wil = 1 - \frac{C}{N} + \frac{C}{P}

    where:

        - C is the number of correct words,
        - N is the number of words in the reference
        - P is the number of words in the prediction


    Args:
        compute_on_step:
            Forward only calls ``update()`` and returns None if this is set to False.

            .. deprecated:: v0.8
                Argument has no use anymore and will be removed v0.9.

        dist_sync_on_step:
            Synchronize metric state across processes at each ``forward()``
            before returning the value at the step.
        process_group:
            Specify the process group on which synchronization is called.
        dist_sync_fn:
            Callback that performs the allgather operation on the metric state. When ``None``, DDP
            will be used to perform the allgather


    Examples:
        >>> from torchmetrics import WordInfoLost
        >>> preds = ["this is the prediction", "there is an other sample"]
        >>> target = ["this is the reference", "there is another one"]
        >>> metric = WordInfoLost()
        >>> metric(preds, target)
        tensor(0.6528)
    """
    is_differentiable = False
    higher_is_better = False
    errors: Tensor
    target_total: Tensor
    preds_total: Tensor

    def __init__(
        self,
        compute_on_step: Optional[bool] = None,
        dist_sync_on_step: bool = False,
        process_group: Optional[Any] = None,
        dist_sync_fn: Callable = None,
    ):
        super().__init__(
            compute_on_step=compute_on_step,
            dist_sync_on_step=dist_sync_on_step,
            process_group=process_group,
            dist_sync_fn=dist_sync_fn,
        )
        self.add_state("errors", tensor(0.0), dist_reduce_fx="sum")
        self.add_state("target_total", tensor(0.0), dist_reduce_fx="sum")
        self.add_state("preds_total", tensor(0.0), dist_reduce_fx="sum")

    def update(self, preds: Union[str, List[str]], target: Union[str, List[str]]) -> None:  # type: ignore
        """Store predictions/references for computing Word Information Lost scores.

        Args:
            preds:
                Transcription(s) to score as a string or list of strings
            target:
                Reference(s) for each speech input as a string or list of strings
        """
        errors, target_total, preds_total = _wil_update(preds, target)
        self.errors += errors
        self.target_total += target_total
        self.preds_total += preds_total

    def compute(self) -> Tensor:
        """Calculate the Word Information Lost.

        Returns:
            Word Information Lost score
        """
        return _wil_compute(self.errors, self.target_total, self.preds_total)
