import { ApiResponse, ScriptError } from '../types';

export type ScriptEvent = {
  // Event type and basic info
  type: 'output' | 'error' | 'complete';
  content?: string;
  is_error?: boolean;
  message?: string;
  success?: boolean;
  
  // Error information
  error?: string | {
    type?: string;
    message?: string;
    traceback?: string;
    suggestions?: string[];
    details?: Record<string, any>;
  };
  error_type?: string;
  error_details?: Record<string, any>;
  
  // Execution context
  stdout?: string;
  stderr?: string;
  traceback?: string;
  returncode?: number;
  
  // Script information
  script_content?: string;
  
  // Additional metadata
  suggestions?: string[];
  possible_causes?: string[];
  page_history?: Array<Record<string, any>>;
  
  // Additional details
  details?: Record<string, any>;
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
  type?: 'output' | 'error' | 'complete';
  content?: string;
  is_error?: boolean;
  message?: string;
  stdout?: string;
  stderr?: string;
  error?: string;
  error_type?: string;
  error_details?: Record<string, any>;
  suggestions?: string[];
  possible_causes?: string[];
  returncode?: number;
  traceback?: string;
  details?: Record<string, any>;
  script_content?: string;
  page_history?: Array<Record<string, any>>;
}

export const runScript = async (options: string | RunScriptOptions): Promise<RunScriptResult> => {
  const scriptId = typeof options === 'string' ? options : options.scriptId;
  const onEvent = typeof options === 'object' ? options.onEvent : undefined;
  
  try {
    const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}/run`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });

    const responseData = await response.json().catch(() => ({
      error: 'Failed to parse server response',
      error_type: 'response_parse_error',
      success: false
    }));
    
    if (!response.ok) {
      // Handle error response
      const errorData: ScriptError = {
        error: responseData.error || responseData.message || 'Failed to execute script',
        error_type: responseData.error_type || 'api_error',
        message: responseData.message || responseData.error || 'An unknown error occurred',
        stderr: responseData.stderr,
        traceback: responseData.traceback,
        details: responseData.details || responseData.error_details || {},
        returncode: responseData.returncode,
        suggestions: Array.isArray(responseData.suggestions) ? responseData.suggestions : [],
        possible_causes: Array.isArray(responseData.possible_causes) ? responseData.possible_causes : [],
        script_content: responseData.script_content,
        type: responseData.type || 'error',
        is_error: true,
        success: false
      };
      
      if (onEvent) {
        onEvent({
          type: 'error',
          content: errorData.error || 'Script execution failed',
          is_error: true,
          message: errorData.message,
          error_type: errorData.error_type,
          stderr: errorData.stderr,
          traceback: errorData.traceback,
          suggestions: errorData.suggestions,
          possible_causes: errorData.possible_causes,
          script_content: errorData.script_content,
          error: {
            type: errorData.error_type || 'execution_error',
            message: errorData.message,
            traceback: errorData.traceback,
            suggestions: errorData.suggestions,
            details: errorData.details
          }
        });
      }
      
      return {
        success: false,
        error: errorData.error,
        error_type: errorData.error_type,
        message: errorData.message,
        stderr: errorData.stderr,
        stdout: responseData.stdout,
        returncode: errorData.returncode,
        details: errorData.details,
        suggestions: errorData.suggestions,
        possible_causes: errorData.possible_causes,
        script_content: errorData.script_content
      };
    }

    // Handle successful response
    const result: RunScriptResult = {
      success: responseData.success === true,
      type: responseData.type || 'complete',
      content: responseData.content || responseData.stdout || '',
      is_error: responseData.is_error || false,
      message: responseData.message,
      stdout: responseData.stdout || '',
      stderr: responseData.stderr || '',
      error: responseData.error,
      error_type: responseData.error_type,
      error_details: responseData.error_details || responseData.details,
      suggestions: Array.isArray(responseData.suggestions) ? responseData.suggestions : [],
      possible_causes: Array.isArray(responseData.possible_causes) ? responseData.possible_causes : [],
      returncode: responseData.returncode,
      traceback: responseData.traceback,
      details: responseData.details || {},
      script_content: responseData.script_content,
      page_history: Array.isArray(responseData.page_history) ? responseData.page_history : []
    };

    // If we have an event callback, send the appropriate event
    if (onEvent) {
      const eventData: ScriptEvent = {
        type: result.type || 'complete',
        content: result.content,
        is_error: result.is_error,
        message: result.message,
        stdout: result.stdout,
        stderr: result.stderr,
        error: result.error ? {
          type: result.error_type || 'ExecutionError',
          message: result.error,
          traceback: result.traceback,
          suggestions: result.suggestions,
          details: result.details || {}
        } : undefined,
        error_type: result.error_type,
        returncode: result.returncode,
        traceback: result.traceback,
        script_content: result.script_content,
        suggestions: result.suggestions,
        possible_causes: result.possible_causes,
        details: result.details || {},
        page_history: result.page_history,
        error_details: result.error_details
      };

      onEvent(eventData);
    }

    return result;
  } catch (error) {
    console.error('Error running script:', error);
    
    const errorObj = error as Error;
    const errorData: ScriptError = {
      error: errorObj.message || 'Failed to execute script',
      error_type: 'NetworkError',
      message: errorObj.message || 'A network error occurred while executing the script',
      type: 'error',
      is_error: true,
      success: false,
      details: { 
        stack: errorObj.stack,
        name: errorObj.name
      },
      suggestions: [
        'Check your network connection',
        'Verify the server is running and accessible',
        'Check the browser console for detailed error information',
        'Try refreshing the page and trying again'
      ],
      possible_causes: [
        'Network connectivity issues',
        'Server is down or unreachable',
        'CORS configuration problems',
        'Browser extension interference'
      ]
    };
    
    if (onEvent) {
      const eventData: ScriptEvent = {
        type: 'error',
        content: errorData.error,
        is_error: true,
        message: errorData.message,
        error_type: errorData.error_type,
        details: errorData.details,
        suggestions: errorData.suggestions,
        possible_causes: errorData.possible_causes,
        error: {
          type: errorData.error_type,
          message: errorData.message,
          details: errorData.details,
          suggestions: errorData.suggestions
        },
        stdout: '',
        stderr: errorObj.message,
        returncode: -1
      };
      onEvent(eventData);
    }
    
    return {
      success: false,
      error: errorData.error,
      error_type: errorData.error_type,
      message: errorData.message,
      details: errorData.details,
      suggestions: errorData.suggestions,
      possible_causes: errorData.possible_causes,
      is_error: true,
      stderr: errorObj.message,
      returncode: -1
    };