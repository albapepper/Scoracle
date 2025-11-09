import React from 'react';

export function MentionsList({ items = [] as any[] }) {
  return (
    <ul>
      {items.map((m, i) => (
        <li key={m.link || i}>{m.title || m.name || 'Mention'}</li>
      ))}
    </ul>
  );
}
export default MentionsList;
