import React from 'react';
import { PromptInfo } from '../../types';

interface PromptDisplayProps {
  prompt: PromptInfo | null;
}

export const PromptDisplay: React.FC<PromptDisplayProps> = ({ prompt }) => {
  if (!prompt) return null;
  
  return (
    <div className="prompt-display">
      <h4>LLM Prompt ({prompt.isRepair ? 'Repair' : 'Generate'}):</h4>
      <div className="prompt-content">
        <pre>{prompt.content}</pre>
      </div>
    </div>
  );
};
