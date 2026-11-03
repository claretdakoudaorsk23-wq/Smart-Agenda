const taskList = document.getElementById('task-list');
const stats = document.getElementById('stats');
const dayInput = document.getElementById('day-input');
const taskInput = document.getElementById('task-input');
const dayLabel = document.getElementById('day-label');
const statusIndicator = document.getElementById('status-indicator');

const formatDate = (value) => {
  const date = new Date(value + 'T00:00:00');
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
};

const setSelectedDay = (value) => {
  dayInput.value = value;
  dayLabel.textContent = `Programme du ${formatDate(value)}`;
  fetchTasks(value);
};

const renderStats = (tasks) => {
  const total = tasks.length;
  const done = tasks.filter((task) => task.done).length;
  const remaining = total - done;

  stats.innerHTML = `
    <div class="stat-card">
      <span class="value">${total}</span>
      <span class="label">Total</span>
    </div>
    <div class="stat-card">
      <span class="value">${done}</span>
      <span class="label">Réalisées</span>
    </div>
    <div class="stat-card">
      <span class="value">${remaining}</span>
      <span class="label">Restantes</span>
    </div>
  `;
};

const renderTasks = (tasks) => {
  if (!tasks.length) {
    taskList.innerHTML = '<li class="empty-state">Aucune tâche planifiée pour cette date.</li>';
    statusIndicator.textContent = 'Aucun plan';
    statusIndicator.style.background = 'rgba(148, 163, 184, 0.14)';
    statusIndicator.style.color = '#d2dcf3';
    return;
  }

  const doneCount = tasks.filter((task) => task.done).length;
  statusIndicator.textContent = doneCount === tasks.length ? 'Tous terminés' : `${doneCount}/${tasks.length} réalisées`;
  statusIndicator.style.background = doneCount === tasks.length ? 'rgba(16, 185, 129, 0.14)' : 'rgba(124, 58, 237, 0.18)';
  statusIndicator.style.color = doneCount === tasks.length ? '#bbf7d0' : '#d9c6ff';

  taskList.innerHTML = tasks
    .map(
      (task) => `
        <li class="task-item">
          <div class="task-main">
            <input class="task-checkbox" type="checkbox" ${task.done ? 'checked' : ''} data-id="${task.id}" data-day="${task.day}" />
            <span class="task-text ${task.done ? 'done' : ''}">${task.title}</span>
          </div>
          <button class="icon-btn" data-delete-id="${task.id}" data-day="${task.day}" aria-label="Supprimer la tâche">✕</button>
        </li>
      `
    )
    .join('');
};

const fetchTasks = async (day) => {
  const response = await fetch(`/api/tasks?day=${encodeURIComponent(day)}`);
  const data = await response.json();
  renderStats(data.tasks);
  renderTasks(data.tasks);
};

const addTask = async () => {
  const title = taskInput.value.trim();
  const day = dayInput.value || new Date().toISOString().slice(0, 10);

  if (!title) {
    alert('Saisis une tâche avant d’ajouter.');
    return;
  }

  const response = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, day }),
  });

  const result = await response.json();
  if (!response.ok) {
    alert(result.message || 'Impossible d’ajouter cette tâche.');
    return;
  }

  taskInput.value = '';
  fetchTasks(day);
};

const toggleTask = async (taskId, day) => {
  const response = await fetch(`/api/tasks/${taskId}/toggle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ day }),
  });

  const result = await response.json();
  if (!response.ok) {
    alert(result.message || 'Erreur lors de la mise à jour.');
    return;
  }

  fetchTasks(day);
};

const deleteTask = async (taskId, day) => {
  const response = await fetch(`/api/tasks/${taskId}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ day }),
  });

  const result = await response.json();
  if (!response.ok) {
    alert(result.message || 'Erreur lors de la suppression.');
    return;
  }

  fetchTasks(day);
};

const closeDay = async () => {
  const day = dayInput.value || new Date().toISOString().slice(0, 10);
  const response = await fetch('/api/close-day', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ day }),
  });

  const result = await response.json();
  if (!response.ok) {
    alert(result.message || 'Erreur lors de la clôture.');
    return;
  }

  alert(result.message);
  fetchTasks(day);
};

document.getElementById('add-task-btn').addEventListener('click', addTask);

taskInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') addTask();
});

dayInput.addEventListener('change', (event) => {
  setSelectedDay(event.target.value);
});

document.getElementById('close-day-btn').addEventListener('click', closeDay);

taskList.addEventListener('change', (event) => {
  const checkbox = event.target.closest('.task-checkbox');
  if (!checkbox) return;
  toggleTask(checkbox.dataset.id, checkbox.dataset.day);
});

taskList.addEventListener('click', (event) => {
  const deleteBtn = event.target.closest('[data-delete-id]');
  if (!deleteBtn) return;
  deleteTask(deleteBtn.dataset.deleteId, deleteBtn.dataset.day);
});

const initialDay = new Date().toISOString().slice(0, 10);
setSelectedDay(initialDay);
