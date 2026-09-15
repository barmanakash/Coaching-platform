import DashboardLayout from './DashboardLayout';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/student' },
  { label: 'My Courses', path: '/student/courses' },
  { label: 'Upcoming Classes', path: '/student/classes' },
  { label: 'Resources', path: '/student/resources' },
  { label: 'My Doubts', path: '/student/doubts' },
  { label: 'Chat', path: '/student/chat' },
  { label: 'Notifications', path: '/student/notifications' },
  { label: 'Profile', path: '/student/profile' },
];

export default function StudentLayout() {
  return <DashboardLayout title="Student Panel" navItems={NAV_ITEMS} />;
}
