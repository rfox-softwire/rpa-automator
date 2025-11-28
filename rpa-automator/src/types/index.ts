export interface ApiResponse {
  status: string;
  message: string;
  script_path?: string;
  script_id?: string;
  script_content?: string;
  is_repair?: boolean;
  prompt_used?: string;
  urls?: string[];
}

export interface PageHistoryItem {
  url: string;
  title?: string;
  timestamp?: string;
  html?: string;
}

export type ScriptErrorType = 
  | 'TimeoutError' 
  | 'ScriptError' 
  | 'ExecutionError' 
  | 'SyntaxError' 
  | 'RuntimeError' 
  | 'NetworkError' 
  | 'ApiError' 
  | 'UnknownError';

export interface ScriptError {
  // Core error information
  error: string;
  error_type?: ScriptErrorType;
  message?: string;
  type?: 'output' | 'error' | 'complete';
  content?: string;
  is_error?: boolean;
  
  // Script execution context
  stderr?: string;
  stdout?: string;
  returncode?: number;
  traceback?: string;
  
  // Script metadata
  script_content?: string;
  script_id?: string;
  script_path?: string;
  
  // Additional context
  timestamp?: string;
  duration?: number; // in seconds
  
  // Response fields
  success?: boolean;
  error_details?: Record<string, any>;
  details?: {
    line_number?: number;
    column_number?: number;
    function_name?: string;
    file_path?: string;
    [key: string]: any;
  };
  
  // User guidance and error handling
  suggestions?: string[];
  possible_causes?: string[];
  
  // Page history for web automation context
  page_history?: PageHistoryItem[];
  
  // Original error (for debugging)
  original_error?: any;
  
  // Error severity
  severity?: 'info' | 'warning' | 'error' | 'critical';
  
  // Additional metadata
  metadata?: Record<string, any>;
}

export interface InstructionFormData {
  content: string;
}

export interface LlmResponse {
  scriptId?: string;
  scriptPath?: string;
  scriptContent?: string;
  isRepaired?: boolean;
}

export interface PromptInfo {
  content: string;
  isRepair: boolean;
}

export interface StatusMessage {
  type: 'success' | 'error' | 'info';
  message: string;
  llmResponse?: LlmResponse;
}
