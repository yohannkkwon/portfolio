import { fetchJSON, renderProjects, fetchGitHubData } from './global.js';

// Show latest 3 projects on home page
const projects = await fetchJSON('./lib/projects.json');
const latestProjects = projects.slice(0, 3);
const projectsContainer = document.querySelector('.projects');
renderProjects(latestProjects, projectsContainer, 'h2');

// Fetch and display GitHub profile stats
const githubData = await fetchGitHubData('yohannkkwon');
const profileStats = document.querySelector('#profile-stats');

if (profileStats) {
  profileStats.innerHTML = `
    <dl>
      <div><dt>Public Repos</dt><dd>${githubData.public_repos}</dd></div>
      <div><dt>Public Gists</dt><dd>${githubData.public_gists}</dd></div>
      <div><dt>Followers</dt><dd>${githubData.followers}</dd></div>
      <div><dt>Following</dt><dd>${githubData.following}</dd></div>
    </dl>
  `;
}
