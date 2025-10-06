import { useState, useCallback } from 'react';
import { PromptInfo, StatusMessage, LlmResponse } from '../types';
import { submitInstruction } from '../services/api';

export const useInstructionForm = (onSubmitSuccess: (data: any) => void) => {
  const [formData, setFormData] = useState({ content: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentPrompt, setCurrentPrompt] = useState<PromptInfo | null>(null);
  const [status, setStatus] = useState<StatusMessage | null>(null);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent, isRepair: boolean = false, scriptError?: any) => {
    e.preventDefault();
    
    if (!formData.content.trim()) {
      setStatus({ type: 'error', message: 'Please enter an instruction' });
      return;
    }

    setCurrentPrompt(null);
    setIsSubmitting(true);
    setStatus(null);
    
    try {
      const response = await submitInstruction(formData.content, isRepair, scriptError);
      
      if (response.prompt_used) {
        setCurrentPrompt({
          content: response.prompt_used,
          isRepair
        });
      }
      
      // Map the snake_case API response to camelCase LlmResponse
      const llmResponse: LlmResponse = {
        scriptId: response.script_id || response.script_path?.split('_').pop()?.split('.')[0],
        scriptPath: response.script_path,
        scriptContent: response.script_content,
        isRepaired: response.is_repair || false
      };
      
      onSubmitSuccess(llmResponse);
      
      setStatus({ 
        type: 'success', 
        message: isRepair ? 'Script repaired successfully' : response.message || 'Script generated successfully',
        llmResponse: llmResponse
      });
      
      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      setStatus({ type: 'error', message: `Error: ${errorMessage}` });
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  }, [formData.content, onSubmitSuccess]);

  return {
    formData,
    isSubmitting,
    currentPrompt,
    status,
    handleInputChange,
    handleSubmit,
    setStatus
  };
};
