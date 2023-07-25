import sys
import os
import torch

from queryexecutor import QueryExecutor


class ModelEditor:

    def __init__(self, query_executor):
        self._query_executor = query_executor
        self._model = self._query_executor.get_model()
        self._tokenizer = self._query_executor.get_tokenizer()
        self._model_name = self._query_executor.get_model_name()
        self._model_device = self._query_executor.get_device()

    def edit_model(self, fact):
        raise NotImplementedError()  # Override in concrete classes

    def restore_model(self):
        raise NotImplementedError()  # Override in concrete classes


class InContextModelEditor(ModelEditor):

    def __init__(self, query_executor: QueryExecutor):
        super().__init__(query_executor)

    def edit_model(self, fact):
        context = fact.get_fact_phrased() + '\n'
        print(f'In Context Editing added context: {context}')
        self._query_executor.set_prompt_context(context)

    def restore_model(self):
        self._query_executor.set_prompt_context('')


class RomeStyleModelEditor(ModelEditor):

    def __init__(self, query_executor):
        self._changed_weights = None
        super().__init__(query_executor)

    @staticmethod
    def _format_fact_for_rome(fact):
        subject = fact.get_subject_label()
        target = fact.get_target_label()
        prompt = fact.get_fact_prompt().replace(subject, '{}')
        return [{'prompt': prompt, 'subject': subject, 'target_new': {'str': target}}]

    def edit_model(self, fact):
        raise NotImplementedError()  # Override in concrete classes

    def restore_model(self):
        if self._changed_weights is None:
            return

        os.chdir('./memit')
        sys.path.append('..')
        from util import nethook

        with torch.no_grad():
            for k, v in self._changed_weights.items():
                nethook.get_parameter(self._model, k)[...] = v.to(self._model_device)

        sys.path.remove('..')
        os.chdir('../..')


class MEMITModelEditor(RomeStyleModelEditor):

    def __init__(self, query_executor):
        super().__init__(query_executor)

    def edit_model(self, fact):
        os.chdir('./memit')
        sys.path.append('..')
        from memit import MEMITHyperParams, apply_memit_to_model

        requests = self._format_fact_for_rome(fact)
        hparams = MEMITHyperParams.from_json(f'hparams/MEMIT/{self._model_name}.json')
        _, self._changed_weights = apply_memit_to_model(self._model, self._tokenizer, requests, hparams, return_orig_weights=True)

        sys.path.remove('..')
        os.chdir('../..')


class ROMEModelEditor(RomeStyleModelEditor):

    def __init__(self, query_executor):
        super().__init__(query_executor)

    def edit_model(self, fact):
        os.chdir('./memit')
        sys.path.append('..')
        from rome import ROMEHyperParams, apply_rome_to_model

        requests = self._format_fact_for_rome(fact)
        hparams = ROMEHyperParams.from_json(f'hparams/ROME/{self._model_name}.json')
        _, self._changed_weights = apply_rome_to_model(self._model, self._tokenizer, requests, hparams, return_orig_weights=True)

        sys.path.remove('..')
        os.chdir('../..')


class MENDModelEditor(RomeStyleModelEditor):

    def __init__(self, query_executor):
        super().__init__(query_executor)

    def edit_model(self, fact):
        os.chdir('./memit')
        sys.path.append('..')
        from baselines.mend import MENDHyperParams, MendRewriteExecutor

        requests = self._format_fact_for_rome(fact)
        hparams = MENDHyperParams.from_json(f'hparams/MEND/{self._model_name}.json')
        _, self._changed_weights = MendRewriteExecutor().apply_to_model(self._model, self._tokenizer, requests, hparams, return_orig_weights=True)

        sys.path.remove('..')
        os.chdir('../..')
