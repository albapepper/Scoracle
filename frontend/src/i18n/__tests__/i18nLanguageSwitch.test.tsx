import i18n from '../index';

test('changes language and returns translated key', async () => {
  expect(i18n.t('language_changed', { lng: 'en' })).toMatch(/Language changed/);
  await i18n.changeLanguage('es');
  expect(i18n.language).toBe('es');
  const msg = i18n.t('language_changed', { lng: 'es' });
  expect(msg).toMatch(/Idioma cambiado/);
});