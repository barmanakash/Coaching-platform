import { Routes, Route, Navigate } from 'react-router-dom';

import Login from '../pages/auth/Login';
import Signup from '../pages/auth/Signup';
import ProtectedRoute from './ProtectedRoute';

import AdminLayout from '../layouts/AdminLayout';
import TeacherLayout from '../layouts/TeacherLayout';
import StudentLayout from '../layouts/StudentLayout';

import AdminDashboard from '../pages/admin/AdminDashboard';
import StudentsPage from '../pages/admin/StudentsPage';
import TeachersPage from '../pages/admin/TeachersPage';
import CoursesPage from '../pages/admin/CoursesPage';
import ApprovalsPage from '../pages/admin/ApprovalsPage';

import TeacherDashboard from '../pages/teacher/TeacherDashboard';
import TeacherMyCourses from '../pages/teacher/TeacherMyCourses';

import StudentDashboard from '../pages/student/StudentDashboard';
import StudentMyCourses from '../pages/student/StudentMyCourses';

import ProfilePage from '../pages/ProfilePage';
import ComingSoon from '../components/ComingSoon';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminDashboard />} />
        <Route path="approvals" element={<ApprovalsPage />} />
        <Route path="students" element={<StudentsPage />} />
        <Route path="teachers" element={<TeachersPage />} />
        <Route path="courses" element={<CoursesPage />} />
      </Route>

      <Route
        path="/teacher"
        element={
          <ProtectedRoute allowedRoles={['teacher']}>
            <TeacherLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<TeacherDashboard />} />
        <Route path="courses" element={<TeacherMyCourses />} />
        <Route path="students" element={<ComingSoon title="My Students" note="You'll see students enrolled in your courses here once enrollment is built." />} />
        <Route path="resources" element={<ComingSoon title="Resources" note="Upload notes, videos, and assignments for your courses here." />} />
        <Route path="classes" element={<ComingSoon title="Classes" note="Schedule and manage live classes here." />} />
        <Route path="doubts" element={<ComingSoon title="Doubts" note="Answer student doubts here." />} />
        <Route path="chat" element={<ComingSoon title="Chat" note="Real-time chat with students is coming soon." />} />
        <Route path="notifications" element={<ComingSoon title="Notifications" />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>

      <Route
        path="/student"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<StudentDashboard />} />
        <Route path="courses" element={<StudentMyCourses />} />
        <Route path="classes" element={<ComingSoon title="Upcoming Classes" note="Live classes you can join will appear here." />} />
        <Route path="resources" element={<ComingSoon title="Resources" note="Course materials will appear here." />} />
        <Route path="doubts" element={<ComingSoon title="My Doubts" note="Ask questions and track teacher replies here." />} />
        <Route path="chat" element={<ComingSoon title="Chat" note="Real-time chat with teachers is coming soon." />} />
        <Route path="notifications" element={<ComingSoon title="Notifications" />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>

      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
