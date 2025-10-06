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
  returncode?: number;
  error_type?: string;
  traceback?: string;
}> => {
  console.log(`[API] Running script with ID: ${scriptId}`);
  const response = await fetch(`${API_BASE_URL}/scripts/${scriptId}/run`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to execute script');
  }
  
  return response.json();
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
