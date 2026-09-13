from typing import Protocol, TypeVar

from app.domains.common.command_context import CommandContext

CommandT_contra = TypeVar("CommandT_contra", contravariant=True)
ResultT_co = TypeVar("ResultT_co", covariant=True)


class CommandHandler(Protocol[CommandT_contra, ResultT_co]):
    async def __call__(
        self,
        command: CommandT_contra,
        context: CommandContext,
    ) -> ResultT_co: ...
