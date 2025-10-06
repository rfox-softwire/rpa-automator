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
      setScriptOutput(prev => prev + 'Starting script execution...\n');
      
      const result = await runScript(scriptId);
      
      if (result.success) {
        console.log('[ScriptExecution] Script executed successfully');
        const output = result.stdout || '';
        console.log(`[ScriptExecution] Script output: ${output.substring(0, 200)}${output.length > 200 ? '...' : ''}`);
        setScriptOutput(prev => prev + (output || 'No output from script'));
        setStatus({ type: 'success', message: 'Script executed successfully' });
      } else {
        console.error('[ScriptExecution] Script execution failed:', result);
        const errorMessage = result.error || result.error_type || 'Script execution failed';
        const errorDetails: ScriptError = {
          error: errorMessage,
          stderr: result.stderr || '',
          stdout: result.stdout || '',
          returncode: result.returncode,
          script_content: scriptContent,
          error_type: result.error_type || 'execution_error',
          traceback: result.traceback || ''
        };
        
        setScriptError(errorDetails);
        setScriptOutput(prev => prev + 
          '\nError: ' + errorMessage +
          (result.stderr ? '\n' + result.stderr : '') +
          (result.traceback ? '\n\nTraceback:\n' + result.traceback : '')
        );
        setStatus({ type: 'error', message: `Script execution failed: ${errorMessage}` });
      }
    } catch (error) {
      console.error('[ScriptExecution] Unexpected error:', error);
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      const errorDetails = error instanceof Error ? error.stack : JSON.stringify(error);
      setScriptOutput(prev => prev + '\nUnexpected error: ' + errorMessage + '\n' + (errorDetails || ''));
      setStatus({ type: 'error', message: `Error: ${errorMessage}` });
      setStatus({ type: 'error', message: `Error: ${errorMessage}` });
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
