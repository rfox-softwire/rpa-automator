import React, { useState, useRef } from 'react';
import TaskListSidebar from './components/Sidebar';
import './App.css';

interface ApiResponse {
  status: string;
  message: string;
  script_path?: string;
  script_id?: string;
  script_content?: string;
}

interface InstructionFormData {
  content: string;
}

const App: React.FC = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);
  const [llmResponse, setLlmResponse] = useState<{scriptId?: string, scriptPath?: string, scriptContent?: string} | null>(null);
  const [scriptOutput, setScriptOutput] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [formData, setFormData] = useState<InstructionFormData>({
    content: ''
  });
  
  const instructionInputRef = useRef<HTMLTextAreaElement>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const runScript = async (scriptId: string) => {
    try {
      setIsRunning(true);
      setSubmitStatus({ type: 'success', message: 'Running script...' });
      setScriptOutput('Executing script...\n');
      
      const response = await fetch(`http://localhost:8000/api/scripts/${scriptId}/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      if (response.ok) {
        const output = result.output || '';
        const error = result.error || '';
        setScriptOutput(prev => prev + output + (error ? '\nErrors:\n' + error : ''));
        setSubmitStatus({ 
          type: result.status as 'success' | 'error', 
          message: result.message 
        });
      } else {
        throw new Error(result.detail || 'Failed to execute script');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to run script';
      setScriptOutput(prev => prev + '\nError: ' + errorMessage);
      setSubmitStatus({ 
        type: 'error', 
        message: `Error: ${errorMessage}` 
      });
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmitInstruction = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!formData.content.trim()) {
      setSubmitStatus({ type: 'error', message: 'Please enter an instruction' });
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus(null);
    setLlmResponse(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/instructions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: formData.content,
        }),
      });

      const data: ApiResponse = await response.json();
      console.log(data)
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to process instruction');
      }

      // Fetch the script content
      const scriptResponse = await fetch(`http://localhost:8000/api/scripts/${data.script_id}`);
      const scriptData = await scriptResponse.json();
      
      // Update the UI with the script creation status and content
      setLlmResponse({
        scriptId: data.script_id,
        scriptPath: data.script_path,
        scriptContent: scriptData.content
      });
      setSubmitStatus({ 
        type: 'success', 
        message: data.message
      });
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      setSubmitStatus({ 
        type: 'error', 
        message: `Error: ${errorMessage}` 
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rpa-dashboard">
      <TaskListSidebar />
      <main className="dashboard-content">
        <section className="dashboard-column">
          <form onSubmit={handleSubmitInstruction} className="instruction-form">
            <h3 className="instruction-form__title">Enter Your Instructions</h3>
            <textarea 
              ref={instructionInputRef}
              name="content"
              value={formData.content}
              onChange={handleInputChange}
              className="instruction-form__input"
              placeholder="Type your instructions here..."
              required
              rows={6}
              disabled={isSubmitting}
            />
            
            <div className="form-actions">
              <div className="button-group">
                <button 
                  type="submit" 
                  className={`instruction-form__submit ${isSubmitting ? 'is-loading' : ''}`}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <span className="spinner"></span>
                      <span>Processing...</span>
                    </>
                  ) : 'Generate Script'}
                </button>
                {llmResponse?.scriptId && (
                  <button 
                    type="button" 
                    className="instruction-form__run"
                    onClick={() => llmResponse.scriptId && runScript(llmResponse.scriptId)}
                  >
                    Run Script
                  </button>
                )}
              </div>
              {submitStatus && (
                <div className={`status-message status-${submitStatus.type}`}>
                  {submitStatus.message}
                </div>
              )}
            </div>
          </form>
        </section>
        
        <section className="dashboard-column">
          <div className="dashboard-card">
            <h3 className="dashboard-card__title">LLM Response</h3>
            <div className="llm-response">
              {llmResponse ? (
                <div className="script-content">
                  <div className="script-info">
                    <p><strong>Script ID:</strong> {llmResponse.scriptId}</p>
                    <p><strong>Path:</strong> {llmResponse.scriptPath}</p>
                  </div>
                  {llmResponse.scriptContent && (
                    <pre className="code-block">
                      <code className="language-python">
                        {llmResponse.scriptContent}
                      </code>
                    </pre>
                  )}
                </div>
              ) : (
                <p className="empty-state">Submit a prompt to generate a script</p>
              )}
            </div>
          </div>
        </section>
        
        <section className="dashboard-column dashboard-column--wide">
          <div className="dashboard-card">
            <div className="dashboard-card__header">
              <h3 className="dashboard-card__title">Output</h3>
              {scriptOutput && (
                <button 
                  className="clear-output"
                  onClick={() => setScriptOutput('')}
                  disabled={isRunning}
                >
                  Clear Output
                </button>
              )}
            </div>
            <div className="output-content">
              {scriptOutput ? (
                <pre>{scriptOutput}</pre>
              ) : (
                <p className="empty-state">Script output will appear here</p>
              )}
            </div>
            <p className="dashboard-card__content">Task output will be displayed here.</p>
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;
