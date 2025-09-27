# IELTS Task 2 Fine-tuning Data Preparation

This module prepares fine-tuning data for IELTS Task 2 scoring by processing the `chillies/IELTS-writing-task-2-evaluation` Hugging Face dataset and mapping it to our score response schema.

## Overview

The pipeline:
1. **Loads** the Hugging Face dataset with columns: `prompt`, `essay`, `evaluation`, `band`
2. **Maps** the data to our `score_response.v1.json` schema structure
3. **Generates** synthetic `evidence_quotes`, `errors`, and `suggestions` using Azure OpenAI
4. **Converts** to the fine-tuning format required by Azure OpenAI
5. **Splits** into training and validation sets
6. **Validates** the output format and provides cost estimates

## Quick Start

### Basic Usage

```bash
# Prepare 1000 examples for fine-tuning
python -m src.cook-training-data.prepare --num-samples 1000 --validation-ratio 0.2

# Use mock mode (no Azure OpenAI calls)
python -m src.cook-training-data.prepare --num-samples 100 --disable-azure

# Process all available data
python -m src.cook-training-data.prepare --validation-ratio 0.15
```

### Demo

```bash
# Run a demonstration with 3 examples
python -m src.cook-training-data.example_usage
```

## Module Structure

- **`data_loader.py`** - Loads and samples from Hugging Face dataset
- **`schema_mapper.py`** - Maps raw data to score response schema
- **`synthetic_generator.py`** - Generates synthetic evidence/errors/suggestions
- **`finetuning_formatter.py`** - Converts to Azure OpenAI fine-tuning format
- **`prepare.py`** - Main preparation script
- **`example_usage.py`** - Demonstration script

## Data Mapping

### Input (Hugging Face Dataset)
```json
{
  "prompt": "Some people believe...",
  "essay": "In today's world...",
  "evaluation": "The essay demonstrates...",
  "band": 7.0
}
```

### Output (Fine-tuning Format)
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an experienced IELTS examiner..."
    },
    {
      "role": "user", 
      "content": "Task 2 Question: ...\n\nScore this essay..."
    },
    {
      "role": "assistant",
      "content": "{\"per_criterion\": [...], \"overall\": 7.0, ...}"
    }
  ]
}
```

## Synthetic Data Generation

Since the original dataset may not contain detailed `evidence_quotes`, `errors`, and `suggestions` for each criterion, the pipeline generates these using Azure OpenAI:

### Evidence Quotes
- Direct verbatim quotes from the essay
- 1-3 quotes per criterion
- Support the assigned band score

### Errors
- Specific issues related to each criterion
- Include problematic text span and correction
- Categorized by type (grammar, lexical, coherence, task, other)

### Suggestions
- Specific improvement recommendations
- 1-3 suggestions per criterion
- Actionable and relevant to the band score

## Configuration

### Command Line Arguments

- `--dataset`: Hugging Face dataset name (default: `chillies/IELTS-writing-task-2-evaluation`)
- `--dataset-split`: Dataset split to use (default: `train`)
- `--num-samples`: Number of samples to process (default: all)
- `--validation-ratio`: Ratio for validation split (default: 0.2)
- `--output-dir`: Output directory (default: `./finetuning_data`)
- `--batch-size`: Batch size for processing (default: 10)
- `--seed`: Random seed (default: 42)
- `--disable-azure`: Use mock mode instead of Azure OpenAI

### Environment Variables

For Azure OpenAI integration:
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_DEPLOYMENT_SCORER`

## Output Files

### Training Data
- `train.jsonl` - Training examples in fine-tuning format
- `validation.jsonl` - Validation examples (if validation_ratio > 0)
- `metadata.json` - Processing metadata and statistics

### Format Validation
The pipeline validates that output files meet Azure OpenAI requirements:
- Correct JSONL format
- Required message structure (system, user, assistant)
- Valid JSON in assistant responses
- Minimum example count recommendations

## Cost Estimation

The pipeline provides cost estimates based on:
- Number of training examples
- Estimated tokens per example
- Azure OpenAI fine-tuning pricing

Example output:
```
Training examples: 1000
Estimated tokens: 1,500,000
Estimated training cost: $12.00
```

## Error Handling

- **Mock Mode**: If Azure OpenAI is unavailable, falls back to mock synthetic data
- **Batch Processing**: Continues processing even if individual batches fail
- **Validation**: Skips invalid examples with warnings
- **Graceful Degradation**: Saves partial results if processing is interrupted

## Integration with Fine-tuning

Once data is prepared:

1. **Upload** JSONL files to Azure Blob Storage
2. **Create** fine-tuning job in Azure OpenAI Studio
3. **Monitor** training progress
4. **Evaluate** the fine-tuned model
5. **Deploy** for production use

## Examples

### Full Production Run
```bash
python -m src.cook-training-data.prepare \
  --num-samples 5000 \
  --validation-ratio 0.15 \
  --output-dir ./production_finetuning_data \
  --batch-size 20
```

### Development/Testing
```bash
python -m src.cook-training-data.prepare \
  --num-samples 50 \
  --disable-azure \
  --output-dir ./test_finetuning_data
```

### Custom Dataset
```bash
python -m src.cook-training-data.prepare \
  --dataset "your-org/custom-ielts-dataset" \
  --dataset-split "validation" \
  --num-samples 1000
```

## Troubleshooting

### Common Issues

1. **Azure OpenAI API errors**: Use `--disable-azure` for testing
2. **Memory issues**: Reduce `--batch-size` or `--num-samples`
3. **Network timeout**: Increase batch processing timeout
4. **Invalid format**: Check validation output and fix schema mapping

### Debug Mode
Set environment variable for detailed logging:
```bash
export PYTHONPATH=.
export LOG_LEVEL=DEBUG
python -m src.cook-training-data.prepare --num-samples 10
```