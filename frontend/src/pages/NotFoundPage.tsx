import React from 'react';
import { Container, Title, Text, Button } from '@mantine/core';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <Container size="md" py="xl" ta="center">
      <Title order={1} mb="lg">404</Title>
      <Title order={2} mb="md">{t('notFound.title')}</Title>
      <Text mb="xl">{t('notFound.message')}</Text>
      <Button component={Link} to="/">{t('notFound.backHome')}</Button>
    </Container>
  );
}
