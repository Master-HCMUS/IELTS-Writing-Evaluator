# Cook Training Data

This directory contains fine-tuning data for IELTS Task 2 essay scoring, prepared from the HuggingFace dataset `chillies/IELTS-writing-task-2-evaluation` using the modular production pipeline.

## Directory Structure

```
cook-training-data/
├── finetuning_data/           # Generated fine-tuning datasets
│   ├── train.jsonl            # Training data (744 examples, 80%)
│   ├── validation.jsonl       # Validation data (187 examples, 20%)  
│   ├── sample_readable.json   # Single example for review
│   └── metadata.json          # Dataset metadata and cost estimation
└── README.md                  # This file
```

## Dataset Overview

- **Source**: `chillies/IELTS-writing-task-2-evaluation` (HuggingFace)
- **Total Processed**: 931 examples (from 1000 samples, 69 failed due to malformed band scores)
- **Split**: 80% training (744 examples) / 20% test (187 examples)
- **Format**: JSONL with system/user/assistant message structure for Azure OpenAI fine-tuning

## Data Format

Each example contains:
- **System prompt**: IELTS examiner instructions with rubric and response structure
- **User prompt**: Task 2 question + essay to be scored
- **Assistant response**: JSON scoring following schema with:
  - Per-criterion assessments (Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy)
  - Overall band score (0-9 in 0.5 increments)
  - Evidence quotes, errors, and suggestions for each criterion

## File Types

- **`.jsonl`**: Compact format for Azure OpenAI fine-tuning (one JSON per line)
- **`_pretty.jsonl`**: Human-readable format with indentation (for review and debugging)
- **`sample_readable.json`**: Single example in pretty format for quick inspection

## Usage

### Command Line Generation
```bash
# From project root
python -m src.cook_training_data.prepare \
  --num-samples 1000 \
  --validation-ratio 0.2 \
  --disable-azure \
  --output-dir ./cook-training-data/finetuning_data

# With Azure OpenAI (requires .env configuration)  
python -m src.cook_training_data.prepare \
  --num-samples 1000 \
  --validation-ratio 0.2 \
  --output-dir ./cook-training-data/finetuning_data
```

### Azure OpenAI Fine-tuning
The `.jsonl` files are ready for Azure OpenAI fine-tuning:

1. Upload `train.jsonl` and `validation.jsonl` to Azure Blob Storage
2. Create fine-tuning job in Azure OpenAI Studio  
3. Use `metadata.json` for cost estimation and configuration tracking

## Generation Details

- **Architecture**: Modular production pipeline with proper error handling
- **Data Source**: HuggingFace dataset with prompt, essay, evaluation, and band columns
- **Schema Compliance**: Converted to score_response.v1.json schema format
- **Synthetic Enhancement**: Evidence quotes, errors, and suggestions (mock or Azure OpenAI generated)
- **Quality Control**: Robust filtering of malformed band scores and validation
- **Cost Estimation**: Provides token estimates and training cost projections

## Next Steps

1. Review sample files for quality
2. Upload to Azure Blob Storage
3. Create Azure OpenAI fine-tuning job
4. Monitor training progress and adjust hyperparameters as needed