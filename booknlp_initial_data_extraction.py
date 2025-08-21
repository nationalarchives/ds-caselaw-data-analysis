from booknlp.booknlp import BookNLP
from pathlib import Path
import torch, os



def remove_position_ids_and_save(model_file, device, save_path):
    # code from example link in in https://github.com/booknlp/booknlp/issues/26
    state_dict = torch.load(model_file, map_location=device)

    if 'bert.embeddings.position_ids' in state_dict:
        print(f'Removing "position_ids" from the state dictionary of {model_file}')
        del state_dict['bert.embeddings.position_ids']

    torch.save(state_dict, save_path)
    print(f'Modified state dict saved to {save_path}')

def process_model_files(model_params, device):
    # code from example link in in https://github.com/booknlp/booknlp/issues/26
    updated_params = {}
    for key, path in model_params.items():
        if isinstance(path, str) and os.path.isfile(path) and path.endswith('.model'):
            save_path = path.replace('.model', '_modified.model')
            remove_position_ids_and_save(path, device, save_path)
            updated_params[key] = save_path
        else:
            updated_params[key] = path
    return updated_params


user_dir = Path.home()

if Path(f'{user_dir}/booknlp_models/entities_google_bert_uncased_L-6_H-768_A-12-v1.0_modified.model').exists():
    model_params = {
        'pipeline': 'entity,quote,supersense,event,coref',
        'model': 'custom',
        'entity_model_path': f'{user_dir}/booknlp_models/entities_google_bert_uncased_L-6_H-768_A-12-v1.0_modified.model',
        'coref_model_path': f'{user_dir}/booknlp_models/coref_google_bert_uncased_L-12_H-768_A-12-v1.0_modified.model',
        'quote_attribution_model_path': f'{user_dir}/booknlp_models/speaker_google_bert_uncased_L-12_H-768_A-12-v1.0.1_modified.model',
        'bert_model_path': f'{user_dir}/.cache/huggingface/hub/'
    }    
else:
    model_params = {
        'pipeline': 'entity,quote,supersense,event,coref',
        'model': 'custom',
        'entity_model_path': f'{user_dir}/booknlp_models/entities_google_bert_uncased_L-6_H-768_A-12-v1.0.model',
        'coref_model_path': f'{user_dir}/booknlp_models/coref_google_bert_uncased_L-12_H-768_A-12-v1.0.model',
        'quote_attribution_model_path': f'{user_dir}/booknlp_models/speaker_google_bert_uncased_L-12_H-768_A-12-v1.0.1.model',
        'bert_model_path': f'{user_dir}/.cache/huggingface/hub/'
    }

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_params = process_model_files(model_params, device)
	
booknlp=BookNLP("en", model_params)



input_folder = "C:/Users/flawrence/Documents/Projects/FCL/Research Area/ds-caselaw-data-analysis/data/processing/test-data"
output_dir = "C:/Users/flawrence/Documents/Projects/FCL/Research Area/booknlp/output"

for file in Path(input_folder).glob("*_body.txt"):  
    judgement_id = Path(file).stem
    booknlp.process(file, output_dir, judgement_id)