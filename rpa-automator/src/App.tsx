import React, { useCallback } from 'react';
import {  } from './components';
import {
  Sidebar,
  InstructionForm, 
  ScriptViewer, 
  OutputPanel, 
  ActionFooter, 
  PromptDisplay 
} from './components';
import { useInstructionForm } from './hooks/useInstructionForm';
import { useScriptExecution } from './hooks/useScriptExecution';
import { LlmResponse } from './types';
import './App.css';

const App: React.FC = () => {
  // Handle script execution state and actions
  const {
    isRunning,
    scriptOutput,
    scriptError,
    status: executionStatus,
    clearOutput,
    executeScript,
    setScriptError,
    setStatus: setExecutionStatus
  } = useScriptExecution();

  // Handle form submission and state
  const handleSubmitSuccess = useCallback((response: LlmResponse) => {
    setScriptError(null);
    setExecutionStatus({ 
      type: 'success', 
      message: response.isRepaired ? 'Script repaired successfully' : 'Script generated successfully' 
    });
  }, [setScriptError, setExecutionStatus]);

  const {
    formData,
    isSubmitting,
    currentPrompt,
    status: formStatus,
    handleInputChange,
    handleSubmit: handleFormSubmit,
    setStatus: setFormStatus
  } = useInstructionForm(handleSubmitSuccess);

  // Combine status from form and execution
  const status = formStatus || executionStatus;
  
  // Handle form submission
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    await handleFormSubmit(e, !!scriptError, scriptError);
  }, [handleFormSubmit, scriptError]);

  // Handle script execution
  const handleRunScript = useCallback(async () => {
    if (scriptError?.script_content && scriptError.script_id) {
      await executeScript(scriptError.script_id, scriptError.script_content);
    } else if (formStatus?.llmResponse?.scriptId && formStatus.llmResponse.scriptContent) {
      await executeScript(formStatus.llmResponse.scriptId, formStatus.llmResponse.scriptContent);
    }
  }, [executeScript, scriptError, formStatus]);

  // Handle script repair
  const handleRepairScript = useCallback(async () => {
    if (!scriptError) return;
    
    try {
      setFormStatus({ type: 'info', message: 'Repairing script...' });
      await handleFormSubmit(
        new Event('submit') as unknown as React.FormEvent, 
        true, 
        scriptError
      );
    } catch (error) {
      console.error('Repair failed:', error);
    }
  }, [handleFormSubmit, scriptError, setFormStatus]);

  return (
    <div className="rpa-dashboard">
      <Sidebar />
      <main className="dashboard-content">
        <section className="dashboard-column">
          <InstructionForm
            formData={formData}
            isSubmitting={isSubmitting}
            hasError={!!scriptError}
            status={status}
            onInputChange={handleInputChange}
            onSubmit={handleSubmit}
          >
            <PromptDisplay prompt={currentPrompt} />
          </InstructionForm>
        </section>
        
        <section className="dashboard-column">
          <ScriptViewer 
            llmResponse={scriptError ? null : formStatus?.llmResponse || null} 
            scriptError={scriptError} 
          />
        </section>
        
        <section className="dashboard-column dashboard-column--wide">
          <OutputPanel 
            output={scriptOutput} 
            onClear={clearOutput} 
            isRunning={isRunning} 
          />
        </section>
      </main>
      
<ActionFooter
        isSubmitting={isSubmitting}
        hasError={!!scriptError}
        isRunning={isRunning}
        isRepairing={isSubmitting && !!scriptError}
        hasScript={!!formStatus?.llmResponse?.scriptId}
        onSubmit={(e: React.FormEvent) => handleSubmit(e)}
        onRun={handleRunScript}
        onRepair={handleRepairScript}
      />
    </div>
  );
};

export default App;
