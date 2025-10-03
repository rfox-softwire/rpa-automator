import React from 'react';
import './Sidebar.css';

const TaskListSidebar: React.FC = () => {
  const tasks = ['Task 1'];
  
  return (
    <nav className="task-sidebar">
      <h2 className="task-sidebar__title">Tasklist</h2>
      <ul className="task-sidebar__list">
        {tasks.map((task, index) => (
          <li key={index} className="task-sidebar__item">
            {task}
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default TaskListSidebar;
