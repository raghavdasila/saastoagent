import { useRouteDeckContract, useRouteDeckCurrentNode } from "@routedeck/react";
import { DatabaseZap, House, KeyRound, LogIn, MailCheck, UserPlus } from "lucide-react";

const NODE_ICONS = Object.freeze({
  "lounge.home": House,
  "lounge.sign_in": LogIn,
  "lounge.register": UserPlus,
  "lounge.forgot_password": KeyRound,
  "lounge.reset_password": KeyRound,
  "lounge.verify_email": MailCheck,
  "lounge.verification_pending": MailCheck,
  "workspace.home": House,
  "sources.home": DatabaseZap,
});

export function WorkspaceNavigation() {
  const contract = useRouteDeckContract();
  const currentNode = useRouteDeckCurrentNode();
  const nodes = Object.values(contract.nodes);
  const groups = [
    { title: "Lounge", nodes: nodes.filter((node) => node.id.startsWith("lounge.")) },
    { title: "Workspace", nodes: nodes.filter((node) => node.id.startsWith("workspace.")) },
    { title: "Sources", nodes: nodes.filter((node) => node.id.startsWith("sources.")) },
  ];

  return (
    <div className="workspace-navigation">
      <h2>Features</h2>
      {groups.map((group) => (
        <section key={group.title} className="workspace-navigation-group">
          <h3>{group.title}</h3>
          <ul>
        {group.nodes.map((node) => {
          const Icon = NODE_ICONS[node.id as keyof typeof NODE_ICONS] ?? House;
          return (
          <li key={node.id} data-current={node.id === currentNode ? "true" : "false"}>
            <span aria-hidden="true"><Icon /></span>
            <div>
              <strong>{node.title}</strong>
              <small>
                {node.id === "lounge.home"
                  ? "Ask about Corpus"
                  : node.id === "lounge.sign_in"
                    ? "Existing account"
                    : node.id === "lounge.register"
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
        </section>
      ))}
    </div>
  );
}
