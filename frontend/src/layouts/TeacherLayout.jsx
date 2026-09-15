import DashboardLayout from './DashboardLayout';

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/teacher' },
  { label: 'My Courses', path: '/teacher/courses' },
  { label: 'My Students', path: '/teacher/students' },
  { label: 'Resources', path: '/teacher/resources' },
  { label: 'Classes', path: '/teacher/classes' },
  { label: 'Doubts', path: '/teacher/doubts' },
  { label: 'Chat', path: '/teacher/chat' },
  { label: 'Notifications', path: '/teacher/notifications' },
  { label: 'Profile', path: '/teacher/profile' },
];

export default function TeacherLayout() {
  return <DashboardLayout title="Teacher Panel" navItems={NAV_ITEMS} />;
}
