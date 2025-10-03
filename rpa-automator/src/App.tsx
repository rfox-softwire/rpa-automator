import React, { useState, useRef } from 'react';
import TaskListSidebar from './components/Sidebar';
import './App.css';

interface ApiResponse {
  status: string;
  message: string;
  filepath?: string;
  response_file?: string;
  llm_response?: {
    id: string;
    object: string;
    created: number;
    model: string;
    choices: Array<{
      index: number;
      message: {
        role: string;
        content: string;
      };
      finish_reason: string;
    }>;
    usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
  };
}

interface InstructionFormData {
  content: string;
  maxTokens: number;
  temperature: number;
}

const App: React.FC = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);
  const [llmResponse, setLlmResponse] = useState<string>('');
  const [formData, setFormData] = useState<InstructionFormData>({
    content: '',
    maxTokens: 200,
    temperature: 0.7,
  });
  
  const instructionInputRef = useRef<HTMLTextAreaElement>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'maxTokens' || name === 'temperature' ? parseFloat(value) : value
    }));
  };

  const handleSubmitInstruction = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!formData.content.trim()) {
      setSubmitStatus({ type: 'error', message: 'Please enter an instruction' });
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus(null);

    setIsSubmitting(true);
    setSubmitStatus(null);
    setLlmResponse('');
    
    try {
      const response = await fetch('http://localhost:8000/api/instructions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: formData.content,
          max_tokens: formData.maxTokens,
          temperature: formData.temperature,
        }),
      });

      const data: ApiResponse = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to process instruction');
      }

      // Update the response in the UI
      if (data.llm_response?.choices?.[0]?.message?.content) {
        setLlmResponse(data.llm_response.choices[0].message.content);
      }
      
      setSubmitStatus({ 
        type: 'success', 
        message: data.message || 'Instruction processed successfully' 
      });
      
      // Reset form
      setFormData(prev => ({ ...prev, content: '' }));
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
            
            <div className="form-controls">
              <div className="form-group">
                <label htmlFor="maxTokens">Max Tokens:</label>
                <input
                  type="number"
                  id="maxTokens"
                  name="maxTokens"
                  min="1"
                  max="2000"
                  value={formData.maxTokens}
                  onChange={handleInputChange}
                  className="form-input"
                  disabled={isSubmitting}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="temperature">Temperature:</label>
                <input
                  type="number"
                  id="temperature"
                  name="temperature"
                  min="0"
                  max="2"
                  step="0.1"
                  value={formData.temperature}
                  onChange={handleInputChange}
                  className="form-input"
                  disabled={isSubmitting}
                />
              </div>
            </div>
            
            <div className="form-actions">
              <button 
                type="submit" 
                className={`instruction-form__submit ${isSubmitting ? 'is-loading' : ''}`}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Processing...' : 'Generate Response'}
              </button>
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
                <div className="response-content">
                  {llmResponse.split('\n').map((line, i) => (
                    <p key={i}>{line || <br />}</p>
                  ))}
                </div>
              ) : (
                <p className="empty-state">Submit a prompt to see the LLM's response here</p>
              )}
            </div>
          </div>
        </section>
        
        <section className="dashboard-column dashboard-column--wide">
          <div className="dashboard-card">
            <h3 className="dashboard-card__title">Output</h3>
            <p className="dashboard-card__content">Task output will be displayed here.</p>
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;
