import { useState, useCallback } from 'react';
import { ScriptError, ScriptErrorType } from '../types';
import { runScript, type ScriptEvent } from '../services/api';

// Type for the status state
type StatusType = 'success' | 'error' | 'info';
interface StatusState {
  type: StatusType;
  message: string;
}

// Type for accumulated script output
interface AccumulatedOutput {
  stdout: string;
  stderr: string;
  error: string | null;
  error_type: string;
  traceback: string;
  suggestions: string[];
  script_content: string;
  details?: Record<string, any>;
}

// Helper function to normalize error type
export const normalizeErrorType = (errorType?: string): ScriptErrorType => {
  if (!errorType) return 'UnknownError';
  
  const normalizedType = errorType.toLowerCase();
  if (normalizedType === 'timeouterror') return 'TimeoutError';
  if (normalizedType === 'syntaxerror') return 'SyntaxError';
  if (normalizedType === 'runtimeerror') return 'RuntimeError';
  if (normalizedType === 'networkerror') return 'NetworkError';
  if (normalizedType === 'apierror') return 'ApiError';
  if (normalizedType === 'scripterror') return 'ScriptError';
  if (normalizedType === 'executionerror') return 'ExecutionError';
  
  return 'UnknownError';
};

// Helper function to create a standardized error object
const createScriptError = (error: any, scriptContent: string = ''): ScriptError => {
  const isError = error instanceof Error;
  const errorMessage = isError ? error.message : String(error);
  
  // Extract error type from different possible properties
  const errorType = 
    error?.error_type || 
    error?.type || 
    (isError ? error.constructor.name : 'ExecutionError');

  // Ensure we have a valid ScriptErrorType
  const normalizedType = normalizeErrorType(errorType);

  // Create base error object
  const scriptError: ScriptError = {
    error: errorMessage,
    error_type: normalizedType,
    stderr: error?.stderr || '',
    stdout: error?.stdout || '',
    script_content: scriptContent,
    timestamp: new Date().toISOString(),
    severity: 'error',
    suggestions: error?.suggestions || [
      'Check the script for syntax errors',
      'Verify all required dependencies are installed',
      'Review the error details below for more information'
    ],
    details: {
      ...(isError ? {
        name: error.name,
        message: error.message,
        stack: error.stack
      } : { error: String(error) }),
      ...(error?.details || {})
    }
  };

  // Add optional properties if they exist
  if (error?.page_history) {
    scriptError.page_history = error.page_history;
  }
  
  if (error?.returncode !== undefined) {
    scriptError.returncode = error.returncode;
  }

  return scriptError;
};

// Helper function to process and display errors
const processAndDisplayError = (
  error: any, 
  scriptContent: string,
  setScriptError: (error: ScriptError | null) => void,
  setScriptOutput: React.Dispatch<React.SetStateAction<string>>,
  setStatus: (status: { type: 'success' | 'error' | 'info'; message: string } | null) => void
) => {
  try {
    const scriptError = createScriptError(error, scriptContent);
    setScriptError(scriptError);
    
    // Add error details to output
    let errorOutput = `\nError: ${scriptError.error}\n`;
    if (scriptError.stderr) errorOutput += `\nError Output:\n${scriptError.stderr}\n`;
    
    // Safely access stack trace
    const stackTrace = (scriptError.details && 'stack' in scriptError.details) 
      ? scriptError.details.stack 
      : null;
    
    if (stackTrace) {
      errorOutput += `\nStack Trace:\n${stackTrace}\n`;
    }
    
    // Update output with error details
    setScriptOutput(prevOutput => {
      const newOutput = prevOutput ? `${prevOutput}\n${errorOutput}` : errorOutput;
      return newOutput;
    });
    
    setStatus({ 
      type: 'error', 
      message: `Script execution failed: ${scriptError.error}` 
    });
  } catch (err) {
    console.error('Error in processAndDisplayError:', err);
    setStatus({ 
      type: 'error',
      message: 'Failed to process error details. See console for more information.'
    });
  }
};

export const useScriptExecution = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [scriptOutput, setScriptOutput] = useState('');
  const [scriptError, setScriptError] = useState<ScriptError | null>(null);
  const [status, setStatus] = useState<StatusState | null>(null);
  
  // Function to safely update script output
  const updateScriptOutput = useCallback((newContent: string) => {
    setScriptOutput(prev => prev + newContent);
  }, []);
  
  // Function to clear script output
  const clearScriptOutput = useCallback(() => {
    setScriptOutput('');
    setScriptError(null);
  }, []);


  const clearOutput = useCallback(() => {
    setScriptOutput('');
    setScriptError(null);
  }, []);

  const executeScript = async (scriptId: string, scriptContent: string): Promise<void> => {
    try {
      console.log(`[ScriptExecution] Starting script execution for ID: ${scriptId}`);
      setIsRunning(true);
      setScriptError(null);
      
      // Initialize output with a starting message
      const startMessage = 'Starting script execution...\n';
      setScriptOutput(startMessage);
      
      // Set initial status
      setStatus({
        type: 'info',
        message: 'Starting script execution...'
      });
      
      // Track the output state
      let currentOutput = startMessage;
      const updateOutput = (newContent: string) => {
        currentOutput += newContent + '\n';
        setScriptOutput(currentOutput);
      };
      
      // Use a flag to track if we've received the final result
      let finalResultReceived = false;
      let accumulatedOutput: AccumulatedOutput = {
        stdout: '',
        stderr: '',
        error: null,
        error_type: 'ExecutionError' as ScriptErrorType,
        traceback: '',
        suggestions: [],
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
              // Ensure the error type is a valid ScriptErrorType
              const errorType = (event.error_type && 
                ['TimeoutError', 'ScriptError', 'ExecutionError'].includes(event.error_type) 
                  ? event.error_type 
                  : 'ExecutionError') as ScriptErrorType;
              
              accumulatedOutput.error_type = errorType;
              
              // Update the UI with the error
              setScriptError({
                error: accumulatedOutput.error,
                error_type: errorType,
                stderr: accumulatedOutput.stderr || '',
                traceback: accumulatedOutput.traceback || '',
                suggestions: Array.isArray(accumulatedOutput.suggestions) ? accumulatedOutput.suggestions : [],
                script_content: accumulatedOutput.script_content || '',
                returncode: -1, // Default error code
                details: event.details
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
                // Handle error event
                const errorDetails = typeof event.error === 'string' 
                  ? { message: event.error }
                  : event.error || {};
                
                // Update error details from the completion event
                accumulatedOutput = {
                  ...accumulatedOutput,
                  error: errorDetails.message || event.message || 'Script execution failed',
                  error_type: errorDetails.type || event.error_type || 'execution_error',
                  traceback: errorDetails.traceback || event.traceback || '',
                  suggestions: errorDetails.suggestions || event.suggestions || [],
                  script_content: event.script_content || accumulatedOutput.script_content,
                  details: errorDetails.details || event.details
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
    } catch (error: unknown) {
      // This catch block is for unexpected errors (like network issues)
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
              const errorDetails: ScriptError = {
                error: errorMessage,
                error_type: 'UnknownError',
                script_content: scriptContent || '',
                traceback: error instanceof Error ? error.stack : undefined,
                stderr: '',
                stdout: '',
                suggestions: [],
                details: error instanceof Error ? { message: error.message, stack: error.stack } : { error: String(error) },
                returncode: -1,
                severity: 'error'
              }; 
      console.error('[ScriptExecution] Unexpected error:', error);
      setScriptError(errorDetails);
      setScriptOutput(prev => prev + `\nUnexpected Error: ${errorMessage}`);
      setStatus({ 
        type: 'error',
        message: `Script execution failed: ${errorMessage}`
      });
    } finally {
      console.log('[ScriptExecution] Script execution completed');
      setIsRunning(false);
    }
  };

  // Helper function to process and display error details
  const processAndDisplayError = useCallback((errorDetails: {
    error?: string | null;
    error_type?: string;  // Allow any string for error_type
    returncode?: number;
    error_details?: any;
    stderr?: string;
    stdout?: string;
    script_content?: string;
    traceback?: string;
    suggestions?: string[];
    details?: any;
  }) => {
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
    const errorToSet: ScriptError = {
      error: errorDetails.error || 'Unknown error occurred',
      error_type: (errorDetails.error_type as ScriptErrorType) || 'ExecutionError',
      stderr: errorDetails.stderr || '',
      stdout: errorDetails.stdout || '',
      returncode: errorDetails.returncode,
      script_content: errorDetails.script_content || '',
      traceback: errorDetails.traceback,
      suggestions: Array.isArray(errorDetails.suggestions) ? errorDetails.suggestions : [],
      details: errorDetails.details || errorDetails.error_details
    };
    setScriptError(errorToSet);
    
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
