import httpx
import pytest
import respx

from app.publishers import MediaItem, PublishRequest
from app.publishers.base import PublishError
from app.publishers.facebook import FacebookPublisher
from app.publishers.linkedin import LinkedInPublisher
from app.publishers.threads import ThreadsPublisher


def img(url="https://cdn.example/p.jpg"):
    return MediaItem(url=url, content_type="image/jpeg", kind="image")


def vid(url="https://cdn.example/v.mp4"):
    return MediaItem(url=url, content_type="video/mp4", kind="video")


# ── Facebook ──────────────────────────────────────────────────────────────────
@respx.mock
async def test_facebook_text_feed():
    route = respx.post(url__regex=r"https://graph\.facebook\.com/.*/123/feed").mock(
        return_value=httpx.Response(200, json={"id": "123_456"})
    )
    result = await FacebookPublisher().publish("123", "tok", PublishRequest(body="hi"))
    assert route.called
    assert result.platform_post_id == "123_456"


@respx.mock
async def test_facebook_single_image():
    route = respx.post(url__regex=r".*/123/photos").mock(
        return_value=httpx.Response(200, json={"id": "p1", "post_id": "123_777"})
    )
    result = await FacebookPublisher().publish(
        "123", "tok", PublishRequest(body="cap", media=[img()])
    )
    assert route.called
    assert result.platform_post_id == "123_777"


@respx.mock
async def test_facebook_multi_image_uses_attached_media():
    photos = respx.post(url__regex=r".*/123/photos").mock(
        side_effect=[
            httpx.Response(200, json={"id": "p1"}),
            httpx.Response(200, json={"id": "p2"}),
        ]
    )
    feed = respx.post(url__regex=r".*/123/feed").mock(
        return_value=httpx.Response(200, json={"id": "123_999"})
    )
    result = await FacebookPublisher().publish(
        "123", "tok", PublishRequest(body="multi", media=[img(), img("https://cdn.example/q.jpg")])
    )
    assert photos.call_count == 2
    assert feed.called
    # attached_media[*] must carry the unpublished photo ids
    sent = feed.calls.last.request.content.decode()
    assert "attached_media%5B0%5D" in sent or "attached_media[0]" in sent
    assert "p1" in sent and "p2" in sent
    assert result.platform_post_id == "123_999"


@respx.mock
async def test_facebook_video():
    route = respx.post(url__regex=r".*/123/videos").mock(
        return_value=httpx.Response(200, json={"id": "vid_1"})
    )
    result = await FacebookPublisher().publish(
        "123", "tok", PublishRequest(body="watch", media=[vid()])
    )
    assert route.called
    assert result.platform_post_id == "vid_1"


@respx.mock
async def test_facebook_rejects_mixed_media():
    with pytest.raises(PublishError):
        await FacebookPublisher().publish(
            "123", "tok", PublishRequest(body="x", media=[img(), vid()])
        )


# ── LinkedIn ──────────────────────────────────────────────────────────────────
@respx.mock
async def test_linkedin_sets_version_header_and_reads_urn():
    captured = {}

    def handler(request):
        captured["version"] = request.headers.get("LinkedIn-Version")
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:789"})

    respx.post("https://api.linkedin.com/rest/posts").mock(side_effect=handler)

    result = await LinkedInPublisher().publish(
        "urn:li:person:abc", "tok", PublishRequest(body="hello")
    )
    assert result.platform_post_id == "urn:li:share:789"
    assert captured["version"]
    assert captured["auth"] == "Bearer tok"


@respx.mock
async def test_linkedin_single_image():
    respx.get("https://cdn.example/p.jpg").mock(return_value=httpx.Response(200, content=b"IMG"))
    init = respx.post(url__regex=r".*/rest/images\?action=initializeUpload").mock(
        return_value=httpx.Response(
            200, json={"value": {"uploadUrl": "https://up.li/img1", "image": "urn:li:image:1"}}
        )
    )
    put = respx.put("https://up.li/img1").mock(return_value=httpx.Response(201))
    post = respx.post("https://api.linkedin.com/rest/posts").mock(
        return_value=httpx.Response(201, headers={"x-restli-id": "urn:li:share:1"})
    )

    result = await LinkedInPublisher().publish(
        "urn:li:person:abc", "tok", PublishRequest(body="pic", media=[img()])
    )
    assert init.called and put.called and post.called
    body = post.calls.last.request.content.decode()
    assert "urn:li:image:1" in body
    assert result.platform_post_id == "urn:li:share:1"


@respx.mock
async def test_linkedin_video_chunked_upload():
    respx.get("https://cdn.example/v.mp4").mock(return_value=httpx.Response(200, content=b"VIDEOBYTES"))
    init = respx.post(url__regex=r".*/rest/videos\?action=initializeUpload").mock(
        return_value=httpx.Response(
            200,
            json={
                "value": {
                    "video": "urn:li:video:9",
                    "uploadToken": "tok9",
                    "uploadInstructions": [
                        {"uploadUrl": "https://up.li/v1", "firstByte": 0, "lastByte": 9}
                    ],
                }
            },
        )
    )
    put = respx.put("https://up.li/v1").mock(return_value=httpx.Response(200, headers={"etag": "etag-1"}))
    finalize = respx.post(url__regex=r".*/rest/videos\?action=finalizeUpload").mock(
        return_value=httpx.Response(200)
    )
    post = respx.post("https://api.linkedin.com/rest/posts").mock(
        return_value=httpx.Response(201, headers={"x-restli-id": "urn:li:share:2"})
    )

    result = await LinkedInPublisher().publish(
        "urn:li:person:abc", "tok", PublishRequest(body="clip", media=[vid()])
    )
    assert init.called and put.called and finalize.called and post.called
    fin_body = finalize.calls.last.request.content.decode()
    assert "etag-1" in fin_body and "urn:li:video:9" in fin_body
    assert result.platform_post_id == "urn:li:share:2"


# ── Threads ────────────────────────────────────────────────────────────────────
@respx.mock
async def test_threads_two_step_publish():
    create = respx.post(url__regex=r"https://graph\.threads\.net/v1\.0/u1/threads\?").mock(
        return_value=httpx.Response(200, json={"id": "container_1"})
    )
    publish = respx.post(
        url__regex=r"https://graph\.threads\.net/v1\.0/u1/threads_publish"
    ).mock(return_value=httpx.Response(200, json={"id": "thread_42"}))

    result = await ThreadsPublisher().publish("u1", "tok", PublishRequest(body="hi"))
    assert create.called and publish.called
    assert result.platform_post_id == "thread_42"


@respx.mock
async def test_threads_single_image_polls_status():
    respx.post(url__regex=r".*/u1/threads\?").mock(
        return_value=httpx.Response(200, json={"id": "c1"})
    )
    status = respx.get(url__regex=r".*/v1\.0/c1\?").mock(
        return_value=httpx.Response(200, json={"status": "FINISHED"})
    )
    publish = respx.post(url__regex=r".*/u1/threads_publish").mock(
        return_value=httpx.Response(200, json={"id": "t_img"})
    )
    result = await ThreadsPublisher().publish(
        "u1", "tok", PublishRequest(body="pic", media=[img()])
    )
    assert status.called and publish.called
    assert result.platform_post_id == "t_img"


@respx.mock
async def test_threads_carousel():
    # Two item containers + one carousel container all POST to /u1/threads.
    create = respx.post(url__regex=r".*/u1/threads\?").mock(
        side_effect=[
            httpx.Response(200, json={"id": "item1"}),
            httpx.Response(200, json={"id": "item2"}),
            httpx.Response(200, json={"id": "carousel1"}),
        ]
    )
    respx.get(url__regex=r".*/v1\.0/item\d\?").mock(
        return_value=httpx.Response(200, json={"status": "FINISHED"})
    )
    publish = respx.post(url__regex=r".*/u1/threads_publish").mock(
        return_value=httpx.Response(200, json={"id": "t_carousel"})
    )
    result = await ThreadsPublisher().publish(
        "u1", "tok", PublishRequest(body="album", media=[img(), img("https://cdn.example/b.jpg")])
    )
    assert create.call_count == 3 and publish.called
    assert result.platform_post_id == "t_carousel"


# ── shared ───────────────────────────────────────────────────────────────────
@respx.mock
async def test_retryable_status_flag():
    respx.post(url__regex=r".*/123/feed").mock(return_value=httpx.Response(503, text="busy"))
    with pytest.raises(PublishError) as exc:
        await FacebookPublisher().publish("123", "tok", PublishRequest(body="hi"))
    assert exc.value.retryable is True
