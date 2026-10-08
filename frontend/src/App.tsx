import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import SystemStatus from "./pages/SystemStatus";
import SetupWizard from "./pages/SetupWizard";
import ProviderSettings from "./pages/ProviderSettings";
import AgentPlayground from "./pages/AgentPlayground";
import VoiceTest from "./pages/VoiceTest";
import TaskRecipes from "./pages/TaskRecipes";
import Permissions from "./pages/Permissions";
import Connectors from "./pages/Connectors";
import CallLogs from "./pages/CallLogs";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<SystemStatus />} />
        <Route path="setup" element={<SetupWizard />} />
        <Route path="providers" element={<ProviderSettings />} />
        <Route path="playground" element={<AgentPlayground />} />
        <Route path="voice" element={<VoiceTest />} />
        <Route path="tasks" element={<TaskRecipes />} />
        <Route path="permissions" element={<Permissions />} />
        <Route path="connectors" element={<Connectors />} />
        <Route path="calls" element={<CallLogs />} />
      </Route>
    </Routes>
  );
}
