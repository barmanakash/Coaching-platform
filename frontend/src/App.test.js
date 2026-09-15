import { render, screen } from '@testing-library/react';
import App from './App';

test('renders login page by default', () => {
  render(<App />);
  const heading = screen.getByText(/welcome back/i);
  expect(heading).toBeInTheDocument();
});
