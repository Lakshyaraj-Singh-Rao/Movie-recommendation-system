const searchInput = document.querySelector("#movie-search");
const searchResults = document.querySelector("#search-results");
const searchStatus = document.querySelector("#search-status");
const recommendButton = document.querySelector("#recommend-button");
const recommendationLimit = document.querySelector("#recommendation-limit");
const recommendationsSection = document.querySelector("#recommendations-section");
const recommendationGrid = document.querySelector("#recommendation-grid");
const recommendationStatus = document.querySelector("#recommendation-status");
const selectedTitle = document.querySelector("#selected-title");
const changeMovieButton = document.querySelector("#change-movie");

let selectedMovie = null;
let searchTimer = null;

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = value ?? "";
  return element.innerHTML;
}

function movieMeta(movie) {
  const rating = movie.vote_average ? `Rating ${movie.vote_average.toFixed(1)}` : "Unrated";
  return rating;
}

function selectMovie(movie) {
  selectedMovie = movie;
  searchInput.value = movie.title;
  searchResults.innerHTML = "";
  searchStatus.textContent = `Selected: ${movie.title}`;
  recommendButton.disabled = false;
}

function renderSearchResults(movies) {
  searchResults.innerHTML = "";
  movies.forEach((movie) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.className = "search-result";
    button.type = "button";
    button.innerHTML = `<span>${escapeHtml(movie.title)}</span><span class="movie-meta">${movieMeta(movie)}</span>`;
    button.addEventListener("click", () => selectMovie(movie));
    item.appendChild(button);
    searchResults.appendChild(item);
  });
}

async function searchMovies(query) {
  if (query.trim().length < 2) {
    searchResults.innerHTML = "";
    searchStatus.textContent = query.trim() ? "Type at least two characters." : "";
    return;
  }

  searchStatus.textContent = "Searching…";
  try {
    const response = await fetch(`/movies/search?q=${encodeURIComponent(query)}&limit=8`);
    if (!response.ok) throw new Error("Search unavailable");
    const movies = await response.json();
    renderSearchResults(movies);
    searchStatus.textContent = movies.length ? "Choose the film you meant." : "No matching titles found.";
  } catch {
    searchResults.innerHTML = "";
    searchStatus.textContent = "Could not search the catalogue. Please try again.";
  }
}

function renderRecommendations(movies) {
  recommendationGrid.innerHTML = movies.map((movie, index) => {
    const overview = movie.overview || "No synopsis is available for this title.";
    const rating = movie.vote_average ? `Rating ${movie.vote_average.toFixed(1)}` : "Unrated";
    return `
      <article class="movie-card">
        <span class="card-number">${String(index + 1).padStart(2, "0")}</span>
        <div>
          <h3>${escapeHtml(movie.title)}</h3>
          <p class="overview">${escapeHtml(overview)}</p>
        </div>
        <div class="card-footer"><span>${rating}</span><span>${Math.round(movie.similarity * 100)}% match</span></div>
      </article>`;
  }).join("");
}

async function getRecommendations() {
  if (!selectedMovie) return;
  recommendButton.disabled = true;
  recommendButton.textContent = "Finding…";
  recommendationsSection.hidden = false;
  selectedTitle.textContent = selectedMovie.title;
  recommendationGrid.innerHTML = "";
  recommendationStatus.textContent = "Looking through similar films…";
  recommendationsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const limit = Number(recommendationLimit.value);
    const response = await fetch(`/recommendations?title=${encodeURIComponent(selectedMovie.title)}&limit=${limit}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not load recommendations");
    renderRecommendations(data);
    recommendationStatus.textContent = data.length ? "" : "No recommendations were found for this film.";
  } catch (error) {
    recommendationStatus.textContent = error.message || "Could not load recommendations. Please try again.";
  } finally {
    recommendButton.disabled = false;
    recommendButton.textContent = "Find similar";
  }
}

searchInput.addEventListener("input", (event) => {
  const query = event.target.value;
  selectedMovie = null;
  recommendButton.disabled = true;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => searchMovies(query), 220);
});

recommendButton.addEventListener("click", getRecommendations);
changeMovieButton.addEventListener("click", () => {
  recommendationsSection.hidden = true;
  searchInput.focus();
  searchInput.select();
});
