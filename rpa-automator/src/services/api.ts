import { ApiResponse, ScriptError } from '../types';

export type ScriptEvent = {
  type: 'output' | 'error' | 'complete';
  content?: string;
  is_error?: boolean;
  message?: string;
  error_type?: string;
  success?: boolean;
  error?: {
    type?: string;
    message?: string;
    traceback?: string;
    suggestions?: string[];
  };
};

const API_BASE_URL = 'http://localhost:8000/api';

export const submitInstruction = async (content: string, isRepair: boolean, scriptError?: ScriptError) => {
  const endpoint = isRepair 
    ? `${API_BASE_URL}/scripts/repair?llm_client=openai` 
    : `${API_BASE_URL}/instructions/?llm_client=openai`;
  
  console.log(`[API] ${isRepair ? 'Repairing' : 'Submitting'} instruction:`, { isRepair, content: content.substring(0, 100) + (content.length > 100 ? '...' : '') });
  
  const requestBody: any = { 
    content: content,
    ...(isRepair && scriptError && {
      error_context: {
        error_type: scriptError.error_type || 'unknown',
        error: scriptError.error,
        stderr: scriptError.stderr,
        traceback: scriptError.traceback
      },
      original_script: scriptError.script_content
    })
  };
  
  console.log(`[API] Making ${isRepair ? 'repair' : 'instruction'} request to:`, endpoint);
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || 'Failed to process instruction');
  }
  
  return response.json() as Promise<ApiResponse>;
};

export const fetchScriptContent = async (scriptId: string): Promise<string | null> => {
  console.log('[API] Fetching script content for ID:', scriptId);
  const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}`);
  if (!response.ok) {
    console.error(`[API] Failed to fetch script content: ${response.status}`);
    return null;
  }
  const data = await response.json();
  return data.content || null;
};

interface RunScriptOptions {
  scriptId: string;
  onEvent?: (event: ScriptEvent) => void;
}

interface RunScriptResult {
  success: boolean;
  stdout?: string;
  stderr?: string;
  error?: string;
  error_type?: string;
  error_details?: any;
  suggestions?: string[];
  returncode?: number;
  traceback?: string;
  details?: any;
  script_content?: string;
}

export const runScript = async (options: string | RunScriptOptions): Promise<RunScriptResult> => {
  const scriptId = typeof options === 'string' ? options : options.scriptId;
  const onEvent = typeof options === 'object' ? options.onEvent : undefined;
  console.log(`[API] Running script with ID: ${scriptId}`);
  
  try {
    const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}/run`, {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
      },
    });

    if (!response.ok || !response.body) {
      const responseData = await response.json().catch(() => ({}));
      
      // If we have an onEvent callback, send the error there
      if (onEvent) {
        onEvent({
          type: 'error',
          message: responseData.error || responseData.detail || 'Failed to execute script',
          error_type: responseData.error_type || 'api_error',
        });
      }
      
      // Return the error in the expected format
      return {
        success: false,
        error: responseData.error || responseData.detail || 'Failed to execute script',
        error_type: responseData.error_type || 'api_error',
        stderr: responseData.stderr || responseData.detail,
        traceback: responseData.traceback,
        details: responseData.error_details || responseData,
        returncode: responseData.returncode,
        suggestions: responseData.suggestions,
        script_content: responseData.script_content
      };
    }

    // If no onEvent callback, fall back to the old behavior
    if (!onEvent) {
      const responseData = await response.json();
      return { 
        success: true, 
        ...responseData,
        error_type: responseData.error_type || (responseData.error ? 'execution_error' : undefined)
      };
    }

    // Handle streaming response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let result: RunScriptResult = { success: true };

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Process complete SSE messages
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          
          try {
            const match = line.match(/^data: (.+)$/m);
            if (!match) continue;
            
            const event = JSON.parse(match[1]) as ScriptEvent;
            
            // Forward the event to the callback
            onEvent(event);
            
            // Update the result with the latest data
            if (event.type === 'complete') {
              result = {
                success: event.success || false,
                ...(event.error && {
                  error: event.error.message,
                  error_type: event.error.type,
                  traceback: event.error.traceback,
                  suggestions: event.error.suggestions,
                }),
              };
            } else if (event.type === 'output') {
              if (event.is_error) {
                result.stderr = (result.stderr || '') + (event.content || '') + '\n';
              } else {
                result.stdout = (result.stdout || '') + (event.content || '') + '\n';
              }
            }
          } catch (e) {
            console.error('Error processing SSE message:', e);
          }
        }
      }
    } finally {
      reader.releaseLock();
    }

    return result;
  } catch (error) {
    console.error('[API] Error executing script:', error);
    
    // If we have an onEvent callback, send the error there
    if (onEvent) {
      onEvent({
        type: 'error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        error_type: 'network_error',
      });
    }
    
    // Return the error in the expected format
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      error_type: 'network_error',
      stderr: error instanceof Error ? error.stack : String(error),
      details: error instanceof Error ? { message: error.message, stack: error.stack } : { error: String(error) }
    };
  }
};