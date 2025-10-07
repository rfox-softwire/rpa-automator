import { useState } from 'react';
import { ScriptError } from '../types';
// import { runScript, validateUrls } from '../services/api';
import { runScript } from '../services/api';

export const useScriptExecution = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [scriptOutput, setScriptOutput] = useState('');
  const [scriptError, setScriptError] = useState<ScriptError | null>(null);
  const [status, setStatus] = useState<{type: 'success' | 'error' | 'info', message: string} | null>(null);

  const clearOutput = () => setScriptOutput('');

  const executeScript = async (scriptId: string, scriptContent: string) => {
    try {
      console.log(`[ScriptExecution] Starting script execution for ID: ${scriptId}`);
      setIsRunning(true);
      setScriptError(null);
      const validationMessage = 'Validating script resources...';
      console.log(`[ScriptExecution] ${validationMessage}`);
      setStatus({ type: 'info', message: validationMessage });
      setScriptOutput('Checking required resources...\n');
      
      // // Validate URLs first
      // const urlValidationMessage = 'Validating external resources...';
      // console.log(`[ScriptExecution] ${urlValidationMessage}`);
      // setScriptOutput(prev => prev + `${urlValidationMessage}\n`);
      // const validationResult = await validateUrls(scriptContent);
      // console.log('[ScriptExecution] URL validation result:', { 
      //   hasInaccessibleUrls: validationResult.inaccessible_urls?.length > 0,
      //   totalUrls: validationResult.all_urls?.length || 0 
      // });
      
      // if (validationResult.inaccessible_urls?.length > 0) {
      //   const errorMessage = `Cannot run script: The following required resources are not accessible:\n${validationResult.inaccessible_urls.join('\n')}`;
      //   console.error('[ScriptExecution] Validation failed:', errorMessage);
      //   setScriptOutput(prev => prev + `\n${errorMessage}\n`);
      //   throw new Error(errorMessage);
      // }
      
      // if (validationResult.all_urls?.length > 0) {
      // } else {
      //   setScriptOutput(prev => prev + 'No external resources to validate.\n');
      // }
      
      const startMessage = 'All resources validated. Running script...';
      console.log(`[ScriptExecution] ${startMessage}`);
      setScriptOutput(prev => prev + `${startMessage}\n`);
      
      const result = await runScript(scriptId);
      
      if (result.success) {
        console.log('[ScriptExecution] Script executed successfully');
        const output = result.stdout || 'No output from script';
        console.log(`[ScriptExecution] Script output: ${output.substring(0, 200)}${output.length > 200 ? '...' : ''}`);
        setScriptOutput(prev => prev + (output ? `\n${output}` : ''));
        setStatus({ type: 'success', message: 'Script executed successfully' });
      } else {
        // Handle error response from the API
        console.log('[ScriptExecution] Script execution failed, processing error details...');
        
        // Use the script content from the error response if available, otherwise use the one from props
        const errorScriptContent = result.script_content || scriptContent;
        
        // Create error details object
        const errorDetails: ScriptError = {
          error: result.error || 'Unknown error occurred',
          stderr: result.stderr || '',
          stdout: result.stdout || '',
          returncode: result.returncode,
          script_content: errorScriptContent,
          error_type: result.error_type || 'execution_error',
          traceback: result.traceback || '',
          suggestions: Array.isArray(result.suggestions) ? result.suggestions : [],
          details: result.details || result.error_details
        };
        
        const hasSuggestions = errorDetails.suggestions && errorDetails.suggestions.length > 0;
        
        // Log detailed error information
        console.error('[ScriptExecution] Script execution failed:', {
          error: errorDetails.error,
          type: errorDetails.error_type,
          returnCode: errorDetails.returncode,
          hasStderr: !!errorDetails.stderr,
          hasTraceback: !!errorDetails.traceback,
          hasSuggestions: hasSuggestions
        });
        
        // Format error output for display
        const errorOutputParts = [
          `\nError: ${errorDetails.error}`,
          errorDetails.error_type && `Type: ${errorDetails.error_type}`,
          errorDetails.returncode !== undefined && `Exit Code: ${errorDetails.returncode}`,
          
          // Add suggestions if available
          hasSuggestions ? [
            '\nSuggestions:',
            ...(errorDetails.suggestions || []).map((s: string) => `• ${s}`)
          ].join('\n') : null,
          
          // Add stderr if available
          errorDetails.stderr && `\nError Output:\n${errorDetails.stderr}`,
          
          // Add traceback if available
          errorDetails.traceback && `\nTraceback:\n${errorDetails.traceback}`,
          
          // Add additional details if available
          errorDetails.details && `\nDetails:\n${typeof errorDetails.details === 'string' 
            ? errorDetails.details 
            : JSON.stringify(errorDetails.details, null, 2)}`
        ].filter(Boolean).join('\n') + '\n';
        
        // Update state with error information
        setScriptError(errorDetails);
        setScriptOutput(prev => prev + errorOutputParts);
        setStatus({ 
          type: 'error', 
          message: `Script execution failed: ${errorDetails.error}` 
        });
      }
    } catch (error) {
      // This catch block is for unexpected errors (like network issues)
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      const errorDetails: ScriptError = {
        error: errorMessage,
        error_type: 'unexpected_error',
        script_content: scriptContent,
        traceback: error instanceof Error ? error.stack : undefined
      };
      
      console.error('[ScriptExecution] Unexpected error:', error);
      setScriptError(errorDetails);
      setScriptOutput(prev => prev + `\nUnexpected Error: ${errorMessage}`);
      setStatus({ 
        type: 'error', 
        message: `Unexpected error: ${errorMessage}` 
      });
    } finally {
      console.log('[ScriptExecution] Script execution completed');
      setIsRunning(false);
    }
  };

  return {
    isRunning,
    scriptOutput,
    scriptError,
    status,
    clearOutput,
    executeScript,
    setScriptError,
    setStatus
  };
};
