def create_crew_member(podcastGuid, body):
    return 'Not implemented', 501


def get_crew_member(crewMemberGuid):
    return 'Not implemented', 501


def patch_crew_member(crewMemberGuid, body):
    return 'Not implemented', 501


def delete_crew_member(crewMemberGuid):
    return 'Not implemented', 501


def create_image_upload_url(crewMemberGuid):
    return {
        'url': 'https://samplebucket.s3.amazonaws.com/crew-members/{}/original.jpg'.format(crewMemberGuid),
        'fields': {
            'Content-Type': 'image/jpeg',
            'Expires': 3600
        }
    }
