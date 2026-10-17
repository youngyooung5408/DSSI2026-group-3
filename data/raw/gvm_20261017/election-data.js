/* 2026 九合一選舉：以 data/election-2026.json 更新縣市內容。 */
(function () {
    'use strict';

    var select = document.getElementById('electionCitySelect');
    var candidateWrap = document.getElementById('electionCandidates');
    var infoWrap = document.getElementById('electionInfoWrap');
    var location = document.querySelector('.electionLocation span');
    var hardTitle = document.getElementById('hardIndexTitle');
    var hardTitleTemplate = hardTitle ? hardTitle.textContent.trim() : '';
    var hardEmbed = document.getElementById('hardIndexEmbed');
    var hardSection = document.querySelector('.pageHardIndex');
    var starTitle = document.getElementById('fiveStarTitle');
    var starTitleTemplate = starTitle ? starTitle.textContent.trim() : '';
    var starEmbed = document.getElementById('fiveStarEmbed');
    var focusTitle = document.querySelector('.pageElectionFocus-title');
    var focusTitleTemplate = focusTitle ? focusTitle.textContent.trim() : '';
    var focusGrid = document.querySelector('.pageElectionFocus .focusGrid');
    var articlesWrap = document.querySelector('.pageElectionFocus-articlesWrap');
    var articlesBox = document.querySelector('.pageElectionFocus-articles');
    var articleSlides = articlesBox && articlesBox.querySelector('.swiper-wrapper');
    var focusSwiper = null;

    if (!select || !candidateWrap || !infoWrap || !location || !hardEmbed ||
        !hardSection || !starEmbed || !focusGrid || !articlesWrap || !articlesBox || !articleSlides) return;

    // 圖表頁以 postMessage 回報自身高度，iframe 依此自動撐高。
    // 各縣市圖表檔的訊息名稱不一（例如 hardIndexChartHeight、ntpRadarChartHeight、ntpFiveStarChartHeight），
    // 因此只要名稱以 ChartHeight 結尾就接收，再依「訊息是哪個 iframe 發出的」決定要調整哪一個，不會互相干擾。
    window.addEventListener('message', function (event) {
        var payload = event.data;
        if (!payload || typeof payload.type !== 'string' || !/ChartHeight$/.test(payload.type)) return;
        var frames = [
            starEmbed.querySelector('.fiveStar-frame'),
            hardEmbed.querySelector('.hardIndex-frame')
        ];
        var frame = null;
        frames.forEach(function (candidate) {
            if (candidate && event.source === candidate.contentWindow) frame = candidate;
        });
        if (!frame) return;
        var height = Number(payload.height);
        if (!Number.isFinite(height) || height <= 0) return;
        frame.style.height = Math.min(3000, Math.max(220, Math.ceil(height))) + 'px';
    });

    function element(tag, className, text) {
        var node = document.createElement(tag);
        if (className) node.className = className;
        if (text != null) node.textContent = text;
        return node;
    }

    function message(text) {
        return element('p', 'election-data-message', text);
    }

    function cityTitleFromMarkup(template, cityName) {
        var separator = template.indexOf('‧');
        return separator === -1 ? template : cityName + template.slice(separator);
    }

    function showLoading() {
        select.disabled = true;
        candidateWrap.replaceChildren(message('資料載入中…'));
        infoWrap.replaceChildren();
        hardEmbed.replaceChildren(message('資料載入中…'));
        starEmbed.replaceChildren(message('資料載入中…'));
        focusGrid.replaceChildren();
        articleSlides.replaceChildren();
        articlesWrap.hidden = true;
        articlesBox.hidden = true;
    }

    function addTextList(parent, heading, values) {
        var section = element('div', 'election-info-section');
        section.appendChild(element('h3', 'election-info-title', heading));
        if (!Array.isArray(values) || !values.length) {
            section.appendChild(element('p', 'election-policy-desc', '資料待補'));
        } else {
            var list = element('ul', 'election-info-list');
            values.forEach(function (value) {
                list.appendChild(element('li', '', value));
            });
            section.appendChild(list);
        }
        parent.appendChild(section);
    }

    function addSectionBody(parent, body) {
        var list = null;
        var lastItem = null;
        var nested = null;
        var numbered = null;
        String(body || '').split(/\r?\n/).forEach(function (rawLine) {
            var line = rawLine.trim();
            if (!line) return;

            var bullet = /^[●•]\s*/.test(line);
            var nestedBullet = bullet && /^[\s\u3000]+[●•]/.test(rawLine);
            var numberedItem = /^\d+[.、．]\s*/.test(line);

            if (numberedItem && lastItem) {
                if (!numbered) {
                    numbered = element('ol', 'election-policy-subnum');
                    lastItem.appendChild(numbered);
                }
                numbered.appendChild(element('li', '', line.replace(/^\d+[.、．]\s*/, '')));
                return;
            }
            if (nestedBullet && lastItem) {
                if (!nested) {
                    nested = element('ul', 'focus-subsub');
                    lastItem.appendChild(nested);
                }
                nested.appendChild(element('li', '', line.replace(/^[●•]\s*/, '')));
                return;
            }
            if (bullet) {
                if (!list) {
                    list = element('ul', 'election-policy-sub');
                    parent.appendChild(list);
                }
                lastItem = element('li', '', line.replace(/^[●•]\s*/, ''));
                list.appendChild(lastItem);
                nested = null;
                numbered = null;
                return;
            }
            list = null;
            lastItem = null;
            nested = null;
            numbered = null;
            parent.appendChild(element('p', 'election-policy-desc', line));
        });
    }

    function addPolicies(parent, policies) {
        var section = element('div', 'election-info-section');
        section.appendChild(element('h3', 'election-info-title', '政見'));
        var entries = policies && Array.isArray(policies.sections) ? policies.sections : [];
        if (!entries.length) {
            section.appendChild(message('資料待補'));
        } else {
            var list = element('ul', 'election-policy-list');
            entries.forEach(function (entry) {
                var item = element('li', 'election-policy-item');
                if (entry.title) item.appendChild(element('p', 'election-policy-title', entry.title));
                addSectionBody(item, entry.body);
                list.appendChild(item);
            });
            section.appendChild(list);
        }
        parent.appendChild(section);
    }

    function renderCandidates(city) {
        candidateWrap.replaceChildren();
        infoWrap.replaceChildren();
        var candidates = Array.isArray(city.candidates) ? city.candidates : [];
        if (!candidates.length) {
            candidateWrap.appendChild(message('候選人資料整理中'));
            return;
        }

        candidates.forEach(function (candidate, index) {
            var card = element('button', 'election-candidate' + (index === 0 ? ' is-active' : ''));
            card.type = 'button';
            card.dataset.candidate = candidate.id;
            card.setAttribute('aria-pressed', index === 0 ? 'true' : 'false');
            card.setAttribute('aria-controls', 'election-info-' + candidate.id);
            var photo = element('span', 'election-candidate-photo');
            photo.style.borderColor = candidate.color || '#8E8E8E';
            if (candidate.photo) {
                var image = element('img');
                image.src = candidate.photo;
                image.alt = candidate.name;
                image.loading = 'lazy';
                image.addEventListener('error', function () {
                    image.hidden = true;
                });
                photo.appendChild(image);
            }
            card.appendChild(photo);
            card.appendChild(element('span', 'election-candidate-name', candidate.name));
            candidateWrap.appendChild(card);

            var box = element('div', 'election-info-box' + (index === 0 ? ' is-active' : ''));
            box.id = 'election-info-' + candidate.id;
            box.dataset.candidate = candidate.id;
            box.style.borderColor = candidate.color || '#8E8E8E';
            box.setAttribute('aria-hidden', index === 0 ? 'false' : 'true');
            var scroll = element('div', 'election-info-scroll');
            scroll.appendChild(element('h3', 'election-info-name', candidate.name));
            addTextList(scroll, '學歷', candidate.education);
            addTextList(scroll, '經歷', candidate.experience);
            addPolicies(scroll, candidate.policies);
            box.appendChild(scroll);
            infoWrap.appendChild(box);

            card.addEventListener('click', function () {
                candidateWrap.querySelectorAll('.election-candidate').forEach(function (other) {
                    var active = other === card;
                    other.classList.toggle('is-active', active);
                    other.setAttribute('aria-pressed', active ? 'true' : 'false');
                });
                infoWrap.querySelectorAll('.election-info-box').forEach(function (other) {
                    var active = other === box;
                    other.classList.toggle('is-active', active);
                    other.setAttribute('aria-hidden', active ? 'false' : 'true');
                });
                scroll.scrollTop = 0;
            });
        });
        candidateWrap.dataset.count = String(candidates.length);
    }

    function renderHardIndex(city) {
        var titleText = cityTitleFromMarkup(hardTitleTemplate, city.name);
        hardTitle.textContent = titleText;
        hardEmbed.replaceChildren();
        var embedUrl = city.hardIndex && city.hardIndex.embedUrl;
        var isAllowedUrl = /^https:\/\/flo\.uri\.sh\//.test(embedUrl || '') ||
            /^data\/hard-index\/[a-z0-9_-]+\.html(?:[?#].*)?$/i.test(embedUrl || '');
        hardSection.hidden = !isAllowedUrl;
        if (!isAllowedUrl) return;

        var frame = element('iframe', 'election-embed-frame hardIndex-frame');
        frame.src = embedUrl;
        frame.title = titleText;
        frame.loading = 'lazy';
        frame.allowFullscreen = true;
        hardEmbed.appendChild(frame);
    }

    function renderFiveStar(city) {
        var titleText = cityTitleFromMarkup(starTitleTemplate, city.name);
        starTitle.textContent = titleText;
        starEmbed.replaceChildren();
        var data = city.fiveStar;
        var embedUrl = data && data.embedUrl;
        var isAllowedUrl = /^https:\/\/flo\.uri\.sh\//.test(embedUrl || '') ||
            /^data\/five-stars\/[a-z0-9_-]+\.html(?:[?#].*)?$/i.test(embedUrl || '');
        if (isAllowedUrl) {
            var frame = element('iframe', 'election-embed-frame fiveStar-frame');
            frame.src = embedUrl;
            frame.title = titleText;
            frame.loading = 'lazy';
            frame.allowFullscreen = true;
            starEmbed.appendChild(frame);
            return;
        }
        starEmbed.appendChild(message(titleText + '圖表資料整理中'));
    }

    function renderFocus(city) {
        var titleText = cityTitleFromMarkup(focusTitleTemplate, city.name);
        focusTitle.textContent = titleText;
        focusGrid.replaceChildren();
        var entries = city.focus && Array.isArray(city.focus.sections) ? city.focus.sections : [];
        if (!entries.length) {
            focusGrid.appendChild(message(titleText + '資料整理中'));
            return;
        }
        entries.forEach(function (entry) {
            var card = element('div', 'focusGrid-item');
            if (entry.title) card.appendChild(element('p', 'election-policy-title', entry.title));
            addSectionBody(card, entry.body);
            focusGrid.appendChild(card);
        });
    }

    function renderArticles(city) {
        if (focusSwiper) {
            focusSwiper.destroy(true, true);
            focusSwiper = null;
        }
        articleSlides.replaceChildren();
        var articles = Array.isArray(city.articles) ? city.articles.filter(function (article) {
            return article && article.title && /^https?:\/\//.test(article.url || '');
        }) : [];
        articlesWrap.hidden = articles.length === 0;
        articlesBox.hidden = articles.length === 0;
        articlesBox.closest('.pageElectionFocus').classList.toggle('has-no-articles', !articles.length);
        if (!articles.length) return;

        articles.forEach(function (article) {
            var link = element('a', 'swiper-slide');
            link.href = article.url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            if (article.image && /^https?:\/\/|^img\//.test(article.image)) {
                var holder = element('div', 'img');
                var image = element('img');
                image.src = article.image;
                image.alt = '';
                image.loading = 'lazy';
                holder.appendChild(image);
                link.appendChild(holder);
            }
            link.appendChild(element('div', 'txt', article.title));
            articleSlides.appendChild(link);
        });
        if (typeof Swiper !== 'undefined' && articles.length > 1) {
            focusSwiper = new Swiper('.swiper-electionFocusSlide', {
                speed: 1000,
                spaceBetween: 30,
                slidesPerView: 1,
                loop: articles.length > 3,
                autoplay: articles.length > 3 ? { delay: 4000, disableOnInteraction: false } : false,
                navigation: {
                    prevEl: '.swiper-electionFocusSlide-prev',
                    nextEl: '.swiper-electionFocusSlide-next'
                },
                breakpoints: {
                    968: { spaceBetween: 30, slidesPerView: Math.min(3, articles.length) },
                    750: { spaceBetween: 30, slidesPerView: Math.min(2, articles.length) }
                }
            });
        }
    }

    function renderCity(city) {
        location.textContent = city.name;
        renderCandidates(city);
        renderHardIndex(city);
        renderFiveStar(city);
        renderFocus(city);
        renderArticles(city);
    }

    // 網址參數 ?city=縣市代號（例如 ?city=taoyuan、?city=new-taipei）：開啟時直接顯示該縣市並換成該縣市標題，
    // 切換縣市時同步更新網址與標題，重新整理或分享出去都會開在同一個縣市。
    // 讀取時另外接受資料代號（newTaipei / new_taipei）與中文縣市名（?city=高雄市、?city=臺中市），不分大小寫。
    // 伺服器上由 index.php 依同一個參數先輸出該縣市的標題、canonical 與分享網址（給 Google / FB / LINE），
    // 這裡負責頁面載入後的顯示與站內切換；代號規則兩邊需一致。
    var CITY_PARAM = 'city';

    // 依縣市更換的標題類標籤（<title>、meta title、og:title、og:site_name）：先記住原文，
    // 切換時把「縣市長最新選情分析」或 index.php 已換好的「台南市長最新選情分析」換成新縣市，各標籤原本的前後文字保留。
    var CITY_TITLE_PATTERN = /(?:縣市|[^｜\s]{2}[縣市])長最新選情分析/;
    var originalTitle = document.title;
    var titleMetaList = Array.prototype.map.call(
        document.querySelectorAll('meta[name="title"], meta[property="og:title"], meta[property="og:site_name"]'),
        function (meta) { return { meta: meta, original: meta.getAttribute('content') || '' }; }
    );

    // 資料的 slug 用底線（new_taipei），網址用連字號（new-taipei）
    function cityUrlSlug(city) {
        return String(city.slug || city.id).toLowerCase().replace(/_/g, '-');
    }

    function normalizeCityKey(value) {
        return String(value || '').trim().toLowerCase().replace(/_/g, '-').replace(/臺/g, '台');
    }

    function cityFromUrl(cities) {
        var value = '';
        try {
            value = new URLSearchParams(window.location.search).get(CITY_PARAM) || '';
        } catch (error) {
            return null;
        }
        var key = normalizeCityKey(value);
        if (!key) return null;
        for (var i = 0; i < cities.length; i++) {
            var city = cities[i];
            if (key === cityUrlSlug(city) || key === normalizeCityKey(city.id) || key === normalizeCityKey(city.name)) {
                return city;
            }
        }
        return null;
    }

    function cityTitleText(text, city) {
        return text.replace(CITY_TITLE_PATTERN, city.name + '長最新選情分析');
    }

    function updateTitle(city) {
        document.title = cityTitleText(originalTitle, city);
        titleMetaList.forEach(function (item) {
            item.meta.setAttribute('content', cityTitleText(item.original, city));
        });
    }

    function syncCityToUrl(city) {
        if (!window.history || typeof window.history.replaceState !== 'function') return;
        try {
            // 只換 city 參數，其他參數（如 utm）與 #錨點 原樣保留；用 replaceState 不會多出「上一頁」紀錄
            var url = new URL(window.location.href);
            url.searchParams.set(CITY_PARAM, cityUrlSlug(city));
            window.history.replaceState(window.history.state, '', url.toString());
        } catch (error) {
            // file:// 預覽等無法改網址的環境就略過，不影響切換縣市
        }
    }

    function useData(data) {
        if (!data || data.schemaVersion !== 1 || !Array.isArray(data.cities)) {
            throw new Error('不支援的資料格式');
        }
        var byId = new Map(data.cities.map(function (city) { return [city.id, city]; }));
        Array.prototype.forEach.call(select.options, function (option) {
            option.disabled = !byId.has(option.value);
        });
        // 網址有指定縣市才換標題；沒帶參數的總頁維持「縣市長最新選情分析」
        var urlCity = cityFromUrl(data.cities);
        var initial = urlCity || byId.get(select.value) || data.cities[0];
        if (!initial) throw new Error('沒有縣市資料');
        select.value = initial.id;
        select.disabled = false;
        renderCity(initial);
        if (urlCity) updateTitle(urlCity);
        select.addEventListener('change', function () {
            var city = byId.get(select.value);
            if (city) {
                renderCity(city);
                updateTitle(city);
                syncCityToUrl(city);
            }
        });
    }

    function showError(error) {
        console.error('選舉資料載入失敗：', error);
        candidateWrap.replaceChildren(message('選舉資料載入失敗，請稍後重試。'));
        hardEmbed.replaceChildren(message('資料暫時無法顯示'));
        starEmbed.replaceChildren(message('資料暫時無法顯示'));
        focusGrid.replaceChildren(message('資料暫時無法顯示'));
    }

    showLoading();
    if (window.location.protocol === 'file:') {
        // Browsers block fetch() for local JSON, but allow sibling script files.
        var previewScript = element('script');
        previewScript.src = 'data/election-2026.preview.js';
        previewScript.onload = function () {
            try {
                useData(window.ELECTION_2026_DATA);
            } catch (error) {
                showError(error);
            }
        };
        previewScript.onerror = function () {
            showError(new Error('找不到本機預覽資料檔'));
        };
        document.head.appendChild(previewScript);
    } else {
        fetch('data/election-2026.json', { cache: 'no-cache' })
            .then(function (response) {
                if (!response.ok) throw new Error('HTTP ' + response.status);
                return response.json();
            })
            .then(useData)
            .catch(showError);
    }
})();
