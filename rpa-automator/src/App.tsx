import React, { useRef } from 'react';
import TaskListSidebar from './components/Sidebar';
import './App.css';

const App: React.FC = () => {
  const instructionInputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmitInstruction = (event: React.FormEvent) => {
    event.preventDefault();
    if (instructionInputRef.current?.value) {
      console.log('Instruction submitted:', instructionInputRef.current.value);
      instructionInputRef.current.value = '';
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
              className="instruction-form__input"
              placeholder="Type your instructions here..."
              required
            />
            <button type="submit" className="instruction-form__submit">
              Submit Instruction
            </button>
          </form>
        </section>
        
        <section className="dashboard-column">
          <div className="dashboard-card">
            <h3 className="dashboard-card__title">Task Details</h3>
            <p className="dashboard-card__content">Task information will appear here.</p>
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
