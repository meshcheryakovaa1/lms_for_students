import { useState, useEffect, useRef } from 'react';
import { getEntries, createEntry, updateEntry, deleteEntry } from '../api/client';

const today = () => new Date().toISOString().split('T')[0];
const EMPTY_FORM = { date: today(), comment: '', file: null };

/* ── Форма создания / редактирования записи ──────────────── */
function EntryForm({ initial = EMPTY_FORM, onSave, onCancel, submitLabel = 'Сохранить запись' }) {
  const [form, setForm] = useState({ ...initial });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef();

  // Сбрасываем форму когда меняется initial (после успешного создания)
  useEffect(() => { setForm({ ...initial }); setError(''); }, [initial?.resetKey]);

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  const handleFile = (e) =>
    setForm((f) => ({ ...f, file: e.target.files[0] || null }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.comment.trim()) { setError('Напишите, что делали на занятии'); return; }
    setError('');
    setSaving(true);
    try {
      const fd = new FormData();
      fd.append('date', form.date);
      fd.append('comment', form.comment.trim());
      if (form.file) fd.append('file', form.file);
      await onSave(fd);
      // Сбрасываем форму после успешного сохранения
      setForm({ date: today(), comment: '', file: null });
      if (fileRef.current) fileRef.current.value = '';
    } catch (err) {
      const d = err.response?.data;
      if (typeof d === 'object') {
        const msgs = Object.entries(d).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ');
        setError(msgs);
      } else {
        setError('Ошибка сохранения. Попробуйте ещё раз.');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="entry-form">
      <div className="form-row">
        <label style={{ maxWidth: 200 }}>Дата занятия
          <input type="date" name="date" value={form.date} onChange={handleChange} required />
        </label>
      </div>

      <label>Что делал на занятии <span className="required-star">*</span>
        <textarea
          name="comment"
          value={form.comment}
          onChange={handleChange}
          rows={4}
          required
          placeholder="Опишите подробно: какую тему разбирали, что получилось, что вызвало трудности..."
        />
      </label>

      <label>Прикрепить файл <span className="field-hint">(домашнее задание, скриншот, код)</span>
        <input type="file" ref={fileRef} onChange={handleFile} />
        {form.file && <span className="file-chosen">Выбран: {form.file.name}</span>}
      </label>

      {error && <p className="error">{error}</p>}

      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Сохранение...' : submitLabel}
        </button>
        {onCancel && (
          <button type="button" className="btn btn-outline" onClick={onCancel}>Отмена</button>
        )}
      </div>
    </form>
  );
}

/* ── Бейдж оценки ─────────────────────────────────────────── */
function GradeBadge({ grade }) {
  if (grade == null) return <span className="badge badge-none">Ожидает оценки</span>;
  const cls = grade >= 7 ? 'good' : grade >= 5 ? 'mid' : 'bad';
  return <span className={`badge badge-${cls}`}>{grade} / 10</span>;
}

/* ── Главная страница журнала ─────────────────────────────── */
export default function StudentJournalPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);   // id редактируемой записи
  const [search, setSearch] = useState('');
  const [resetKey, setResetKey] = useState(0);    // для сброса формы после создания

  const load = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      const { data } = await getEntries(params);
      setEntries(data.results ?? data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [search]);

  const handleCreate = async (fd) => {
    await createEntry(fd);
    setResetKey((k) => k + 1);   // триггер сброса формы
    load();
  };

  const handleUpdate = async (fd) => {
    await updateEntry(editing, fd);
    setEditing(null);
    load();
  };

  const handleDelete = async (id) => {
    if (!confirm('Удалить запись?')) return;
    await deleteEntry(id);
    load();
  };

  return (
    <div className="page">
      <h1 className="page-title">Мой журнал занятий</h1>

      {/* ── Форма новой записи — всегда видна ── */}
      <div className="card new-entry-card">
        <div className="new-entry-header">
          <span className="new-entry-icon">✏️</span>
          <h2>Новая запись</h2>
        </div>
        <EntryForm
          initial={{ ...EMPTY_FORM, resetKey }}
          onSave={handleCreate}
          submitLabel="Добавить в журнал"
        />
      </div>

      {/* ── Список прошлых записей ── */}
      <div className="section-header">
        <h2>История записей</h2>
        <div className="search-bar" style={{ margin: 0 }}>
          <input
            placeholder="Поиск по тексту..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="spinner">Загрузка...</div>
      ) : entries.length === 0 ? (
        <div className="empty">
          Записей пока нет — заполни форму выше и добавь первую!
        </div>
      ) : (
        <div className="entries-list">
          {entries.map((entry) => (
            <div key={entry.id} className="card entry-card">
              {editing === entry.id ? (
                <>
                  <h3>Редактирование</h3>
                  <EntryForm
                    initial={{ date: entry.date, comment: entry.comment, file: null }}
                    onSave={handleUpdate}
                    onCancel={() => setEditing(null)}
                    submitLabel="Сохранить изменения"
                  />
                </>
              ) : (
                <>
                  <div className="entry-header">
                    <span className="entry-date">{entry.date}</span>
                    <GradeBadge grade={entry.grade} />
                  </div>
                  <p className="entry-comment">{entry.comment}</p>
                  {entry.file_url && (
                    <a href={entry.file_url} target="_blank" rel="noreferrer" className="file-link">
                      📎 {entry.file_name}
                    </a>
                  )}
                  {entry.graded_by && (
                    <p className="graded-by">Оценил: {entry.graded_by}</p>
                  )}
                  <div className="entry-actions">
                    <button className="btn btn-sm" onClick={() => setEditing(entry.id)}>
                      ✏️ Редактировать
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(entry.id)}>
                      🗑 Удалить
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
