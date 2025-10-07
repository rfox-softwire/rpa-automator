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

export interface ScriptError {
  error: string;
  stderr?: string;
  stdout?: string;
  returncode?: number;
  script_content?: string;
  script_id?: string;
  script_path?: string;
  error_type?: string;
  traceback?: string;
  page_history?: PageHistoryItem[];
  suggestions?: string[];
  details?: any;
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
