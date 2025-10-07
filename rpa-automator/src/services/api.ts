import { ApiResponse, ScriptError } from '../types';

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

export const runScript = async (scriptId: string): Promise<{
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
}> => {
  console.log(`[API] Running script with ID: ${scriptId}`);
  try {
    const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}/run`, {
      method: 'POST',
    });
    
    const responseData = await response.json().catch(() => ({}));
    
    if (!response.ok) {
      // Structure the error response to match the expected ScriptError type
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
    
    return { 
      success: true, 
      ...responseData,
      // Ensure we always have an error_type for consistency
      error_type: responseData.error_type || (responseData.error ? 'execution_error' : undefined)
    };
  } catch (error) {
    console.error('[API] Error executing script:', error);
    // Handle network errors or invalid JSON responses
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
      error_type: 'network_error',
      stderr: error instanceof Error ? error.stack : String(error),
      details: error instanceof Error ? { message: error.message, stack: error.stack } : { error: String(error) }
    };
  }
};

// export const validateUrls = async (scriptContent: string) => {
//   console.log('[API] Validating URLs in script content');
//   const response = await fetch(`${API_BASE_URL}/scripts/validate-urls`, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify({ script_content: scriptContent })
//   });

//   if (!response.ok) {
//     const error = await response.json().catch(() => ({}));
//     throw new Error(error.detail || 'Failed to validate URLs');
//   }

//   return response.json();
// };
