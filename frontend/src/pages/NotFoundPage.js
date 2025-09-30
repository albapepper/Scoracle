import React from 'react';
import { Container, Title, Text, Button } from '@mantine/core';
import { Link } from 'react-router-dom';

function NotFoundPage() {
  return (
    <Container size="md" py="xl" ta="center">
      <Title order={1} mb="lg">404</Title>
      <Title order={2} mb="md">Page Not Found</Title>
      <Text mb="xl">
        The page you're looking for doesn't exist or has been moved.
      </Text>
      <Button component={Link} to="/">
        Back to Home
      </Button>
    </Container>
  );
}

export default NotFoundPage;