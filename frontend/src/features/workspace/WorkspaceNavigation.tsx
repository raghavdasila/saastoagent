import { useRouteDeckContract, useRouteDeckCurrentNode } from "@routedeck/react";
import { DatabaseZap, House, KeyRound, LogIn, MailCheck, UserPlus } from "lucide-react";

const NODE_ICONS = Object.freeze({
  "workspace.lounge": House,
  "workspace.sign_in": LogIn,
  "workspace.register": UserPlus,
  "workspace.forgot_password": KeyRound,
  "workspace.reset_password": KeyRound,
  "workspace.verify_email": MailCheck,
  "workspace.home": House,
  "sources.home": DatabaseZap,
});

export function WorkspaceNavigation() {
  const contract = useRouteDeckContract();
  const currentNode = useRouteDeckCurrentNode();

  return (
    <div className="workspace-navigation">
      <h2>Workspace</h2>
      <ul>
        {Object.values(contract.nodes).map((node) => {
          const Icon = NODE_ICONS[node.id as keyof typeof NODE_ICONS] ?? House;
          return (
          <li key={node.id} data-current={node.id === currentNode ? "true" : "false"}>
            <span aria-hidden="true"><Icon /></span>
            <div>
              <strong>{node.title}</strong>
              <small>
                {node.id === "workspace.lounge"
                  ? "Ask about Corpus"
                  : node.id === "workspace.sign_in"
                    ? "Existing account"
                    : node.id === "workspace.register"
                      ? "New account"
                      : node.id === "workspace.home"
                        ? "Owner Workspace"
                        : node.id === "sources.home"
                          ? "Connector debug"
                        : "Account recovery"}
              </small>
            </div>
          </li>
        )})}
      </ul>
    </div>
  );
}
