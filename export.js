let highlightsLen = 0
let articlesLen = 0
let highlightsUrls = []

const keyBy = (array, key) => (array || []).reduce((r, x) => ({ ...r, [key ? x[key] : x]: x }), {});

const getStore = (key, db) => {
  const transaction = db.transaction(key)
  return transaction.objectStore(key)
}

const getSpaces = async (db) => {
  let spaces = getStore('customLists', db).getAll();
  let spaceItems = getStore('pageListEntries', db).getAll()
  await new Promise(resolve => {
    setTimeout(resolve, 1000);
  });

  spaces = keyBy(spaces.result, 'id')
  spaceItems = spaceItems.result.reduce((obj, item) => {
    return {
      ...obj,
      [item.pageUrl]: [...obj[item.pageUrl] || [], spaces[item.listId].name],
    };
  }, {});
  return spaceItems
}


const sendHighlights = async (db, spaces) => {
  const annotations = getStore('annotations', db).getAll();
  annotations.onsuccess = async function () {
    if (annotations.result.length !== highlightsLen) {
      const groupedData = annotations.result.reduce((result, element) => {
        const pageUrl = element.pageUrl
        const id = element.url.substring(element.url.lastIndexOf("#") + 1);
        result[pageUrl] = result[pageUrl] || {
          annotations: [],
          original_title: element.pageTitle,
          date: new Date(0),
          tags: spaces[pageUrl]
        }
        // last annotation date
        result[pageUrl].date = new Date(result[pageUrl].date).getTime() > element.lastEdited.getTime() ? result[pageUrl].date : element.lastEdited.toISOString()

        result[pageUrl].annotations.push({
          body: element.body.replace(/\n\n/g, "\nㅤ\n") + "\nㅤ\n",
          comment: element.comment,
          position: element.selector.descriptor.content[1].start,
          url: `https://${element.url}`,
          id,
        })

        return result;
      }, {})

      highlightsUrls = Object.keys(groupedData)

      await fetch('http://10.0.0.100:8000/articles/load-highlights', {
        method: 'POST', headers: {
          'Accept': 'application/json', 'Content-Type': 'application/json'
        }, body: JSON.stringify(groupedData)
      })

      highlightsLen = annotations.result.length
    }

    sendArticles(db, spaces)

    annotations.oncomplete = function () {
      db.close();
    };
  }
}


const sendArticles = (db, spaces) => {
  const pages = getStore('pages', db).getAll();
  pages.onsuccess = function () {
    if (pages.result.length !== articlesLen) {
      const groupedData = pages.result.reduce((result, element) => {
        const pageUrl = element.url
        if (!highlightsUrls.includes(pageUrl)) {
          result[pageUrl] = {
            original_title: element.fullTitle,
            tags: spaces[pageUrl]
          }
        }
        return result;
      }, {})

      fetch('http://10.0.0.100:8000/articles/load-articles', {
        method: 'POST', headers: {
          'Accept': 'application/json', 'Content-Type': 'application/json'
        }, body: JSON.stringify(groupedData)
      })

      articlesLen = pages.result.length
    }

  }
}

const run = function (reset = true) {
  if (reset) {
    highlightsLen = 0;
    articlesLen = 0;
  }

  const request = indexedDB.open("memex");
  request.onsuccess = async function () {
    const db = request.result;

    const spaces = await getSpaces(db)
    await sendHighlights(db, spaces, reset)
  }
}

run()

setInterval(() => {
  if (highlightsLen && articlesLen) {
    run(false)
  }
}, 5 * 1000
)
