import { useState, useCallback } from 'react';
import { ScriptError } from '../types';
import { runScript, type ScriptEvent } from '../services/api';

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
      setScriptOutput('');
      
      const startMessage = 'Running script...';
      console.log(`[ScriptExecution] ${startMessage}`);
      setScriptOutput(prev => prev + `${startMessage}\n`);
      
      // Use a flag to track if we've received the final result
      let finalResultReceived = false;
      let accumulatedOutput = {
        stdout: '',
        stderr: '',
        error: null as string | null,
        error_type: '',
        traceback: '',
        suggestions: [] as string[],
        script_content: scriptContent
      };

      // Process streaming response
      const result = await runScript({
        scriptId,
        onEvent: (event: ScriptEvent) => {
          try {
            // Handle different types of events from the server
            if (event.type === 'output') {
              const content = event.content || '';
              if (event.is_error) {
                accumulatedOutput.stderr += content + '\n';
              } else {
                accumulatedOutput.stdout += content + '\n';
              }
              // Update the UI with the latest output
              setScriptOutput(prev => prev + content + '\n');
            } 
            // Handle error event
            else if (event.type === 'error') {
              accumulatedOutput.error = event.message || 'Script execution failed';
              accumulatedOutput.error_type = event.error_type || 'execution_error';
              
              // Update the UI with the error
              setScriptError({
                error: accumulatedOutput.error,
                error_type: accumulatedOutput.error_type,
                stderr: accumulatedOutput.stderr,
                traceback: accumulatedOutput.traceback,
                suggestions: accumulatedOutput.suggestions,
                script_content: accumulatedOutput.script_content
              });
              
              setStatus({ 
                type: 'error', 
                message: `Script execution failed: ${accumulatedOutput.error}` 
              });
            }
            // Handle completion event
            else if (event.type === 'complete') {
              finalResultReceived = true;
              
              if (event.success) {
                console.log('[ScriptExecution] Script executed successfully');
                setStatus({ 
                  type: 'success', 
                  message: 'Script executed successfully' 
                });
              } else {
                // Update error details from the completion event
                accumulatedOutput = {
                  ...accumulatedOutput,
                  error: event.error?.message || 'Script execution failed',
                  error_type: event.error?.type || 'execution_error',
                  traceback: event.error?.traceback || '',
                  suggestions: event.error?.suggestions || []
                };
                
                // Format and display the error
                processAndDisplayError(accumulatedOutput);
              }
            }
          } catch (e) {
            console.error('[ScriptExecution] Error processing stream event:', e);
          }
        },
      });
      
      // If we didn't get a completion event, process the final result
      if (!finalResultReceived) {
        if (result.success) {
          console.log('[ScriptExecution] Script executed successfully');
          setScriptOutput(prev => prev + (result.stdout || 'No output from script'));
          setStatus({ type: 'success', message: 'Script executed successfully' });
        } else {
          processAndDisplayError({
            ...result,
            script_content: result.script_content || scriptContent
          });
        }
      }
    } catch (error) {
      // This catch block is for unexpected errors (like network issues)
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      const errorDetails: ScriptError = {
        error: errorMessage,
        error_type: 'unexpected_error',
        script_content: scriptContent || '',
        traceback: error instanceof Error ? error.stack : undefined,
        stderr: '',
        stdout: '',
        suggestions: [],
        details: error instanceof Error ? { message: error.message, stack: error.stack } : { error: String(error) },
        returncode: -1
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

  // Helper function to process and display error details
  const processAndDisplayError = useCallback((errorDetails: any) => {
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
      errorDetails.details && `\nDetails:\n${
        typeof errorDetails.details === 'string' 
          ? errorDetails.details 
          : JSON.stringify(errorDetails.details, null, 2)
      }`
    ].filter(Boolean).join('\n') + '\n';
    
    // Update state with error information
    setScriptError({
      error: errorDetails.error || 'Unknown error occurred',
      error_type: errorDetails.error_type || 'execution_error',
      stderr: errorDetails.stderr || '',
      stdout: errorDetails.stdout || '',
      returncode: errorDetails.returncode,
      script_content: errorDetails.script_content,
      traceback: errorDetails.traceback,
      suggestions: Array.isArray(errorDetails.suggestions) ? errorDetails.suggestions : [],
      details: errorDetails.details || errorDetails.error_details
    });
    
    setScriptOutput(prev => prev + errorOutputParts);
    setStatus({ 
      type: 'error', 
      message: `Script execution failed: ${errorDetails.error || 'Unknown error'}` 
    });
  }, []);

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
