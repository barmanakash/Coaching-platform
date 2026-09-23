import { useEffect, useState } from 'react';
import {
  Typography, Paper, Box, TextField, Button, Alert, CircularProgress,
  Grid, Chip, Stack, IconButton, Divider, Autocomplete,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { getMyInstitute, updateMyInstitute } from '../../services/api/instituteApi';
import { apiErrorMessage } from '../../utils/roleHome';
import { useAuth } from '../../context/AuthContext';

const EMPTY_PROFILE = { name: '', address: '', phone: '', email: '', website: '', description: '' };
const EMPTY_ACADEMIC = { academic_year: '', subjects: [], classes: [], departments: [], grading: [] };

function TagListEditor({ label, values, onChange }) {
  return (
    <Autocomplete
      multiple
      freeSolo
      options={[]}
      value={values}
      onChange={(_e, newValue) => onChange(newValue)}
      renderTags={(value, getTagProps) =>
        value.map((option, index) => (
          <Chip label={option} size="small" {...getTagProps({ index })} key={option} />
        ))
      }
      renderInput={(params) => (
        <TextField {...params} label={label} placeholder="Type and press Enter" margin="normal" />
      )}
    />
  );
}

export default function SettingsPage() {
  const { updateInstituteName } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saved, setSaved] = useState(false);
  const [code, setCode] = useState('');

  const [profile, setProfile] = useState(EMPTY_PROFILE);
  const [academic, setAcademic] = useState(EMPTY_ACADEMIC);

  useEffect(() => {
    getMyInstitute()
      .then((data) => {
        setCode(data.code);
        setProfile({
          name: data.name, address: data.address, phone: data.phone,
          email: data.email, website: data.website, description: data.description,
        });
        setAcademic(data.academic);
      })
      .catch(() => setError('Could not load institute settings.'))
      .finally(() => setLoading(false));
  }, []);

  const addGradeBand = () => {
    setAcademic((a) => ({ ...a, grading: [...a.grading, { grade: '', min_percent: 0 }] }));
  };
  const updateGradeBand = (index, field, value) => {
    setAcademic((a) => ({
      ...a,
      grading: a.grading.map((band, i) => (i === index ? { ...band, [field]: value } : band)),
    }));
  };
  const removeGradeBand = (index) => {
    setAcademic((a) => ({ ...a, grading: a.grading.filter((_b, i) => i !== index) }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaveError('');
    setSaved(false);
    setSaving(true);
    try {
      const updated = await updateMyInstitute({
        ...profile,
        academic: {
          ...academic,
          grading: academic.grading.map((b) => ({ ...b, min_percent: Number(b.min_percent) || 0 })),
        },
      });
      setProfile({
        name: updated.name, address: updated.address, phone: updated.phone,
        email: updated.email, website: updated.website, description: updated.description,
      });
      setAcademic(updated.academic);
      updateInstituteName(updated.name);
      setSaved(true);
    } catch (err) {
      setSaveError(apiErrorMessage(err, 'Could not save changes.'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <CircularProgress />;

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>Institute Settings</Typography>
        <Chip label={`Code: ${code}`} variant="outlined" />
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {saveError && <Alert severity="error" sx={{ mb: 2 }}>{saveError}</Alert>}
      {saved && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSaved(false)}>Settings saved.</Alert>}

      <Box component="form" onSubmit={handleSave}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" fontWeight={700} mb={2}>Profile</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Institute Name" fullWidth required
                value={profile.name} onChange={(e) => setProfile((p) => ({ ...p, name: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Phone" fullWidth
                value={profile.phone} onChange={(e) => setProfile((p) => ({ ...p, phone: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Email" type="email" fullWidth
                value={profile.email} onChange={(e) => setProfile((p) => ({ ...p, email: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Website" fullWidth placeholder="https://"
                value={profile.website} onChange={(e) => setProfile((p) => ({ ...p, website: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Address" fullWidth
                value={profile.address} onChange={(e) => setProfile((p) => ({ ...p, address: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Description" fullWidth multiline minRows={2}
                value={profile.description} onChange={(e) => setProfile((p) => ({ ...p, description: e.target.value }))}
              />
            </Grid>
          </Grid>
        </Paper>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" fontWeight={700} mb={2}>Academic Configuration</Typography>
          <TextField
            label="Academic Year" placeholder="e.g. 2026-27" sx={{ mb: 1, width: 220 }}
            value={academic.academic_year} onChange={(e) => setAcademic((a) => ({ ...a, academic_year: e.target.value }))}
          />
          <TagListEditor label="Subjects" values={academic.subjects} onChange={(v) => setAcademic((a) => ({ ...a, subjects: v }))} />
          <TagListEditor label="Classes / Grades" values={academic.classes} onChange={(v) => setAcademic((a) => ({ ...a, classes: v }))} />
          <TagListEditor label="Departments" values={academic.departments} onChange={(v) => setAcademic((a) => ({ ...a, departments: v }))} />

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle1" fontWeight={600} mb={1}>Grading Scale</Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            One band must start at 0%, so every score gets a grade.
          </Typography>
          <Stack spacing={1.5}>
            {academic.grading.map((band, index) => (
              <Stack direction="row" spacing={1.5} alignItems="center" key={index}>
                <TextField
                  label="Grade" size="small" sx={{ width: 120 }}
                  value={band.grade} onChange={(e) => updateGradeBand(index, 'grade', e.target.value)}
                />
                <TextField
                  label="Min %" size="small" type="number" sx={{ width: 120 }}
                  value={band.min_percent} onChange={(e) => updateGradeBand(index, 'min_percent', e.target.value)}
                />
                <IconButton size="small" color="error" onClick={() => removeGradeBand(index)}>
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Stack>
            ))}
          </Stack>
          <Button startIcon={<AddIcon />} onClick={addGradeBand} sx={{ mt: 1.5 }}>
            Add grade band
          </Button>
        </Paper>

        <Button type="submit" variant="contained" size="large" disabled={saving}>
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>
      </Box>
    </>
  );
}
